# =============================================================================
# src/migrator.py — Motor de migração Jobber → JobTread
# =============================================================================

import time
import json
from datetime import datetime
from pathlib import Path

from src.jobber_client  import JobberClient
from src.jobtread_client import JobTreadClient
from src.mapper          import map_quote, preview_mapping

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class MigrationResult:
    def __init__(self, quote_id: str, jt_job_id: str):
        self.quote_id    = quote_id
        self.jt_job_id   = jt_job_id
        self.quote_title = ""
        self.items_total = 0
        self.items_ok    = 0
        self.items_failed= 0
        self.errors      = []
        self.skipped     = False
        self.skip_reason = ""
        self.started_at  = datetime.now()
        self.finished_at = None

    @property
    def success(self):
        return not self.skipped and self.items_failed == 0 and self.items_ok > 0

    def to_dict(self):
        return {
            "quote_id":     self.quote_id,
            "jt_job_id":    self.jt_job_id,
            "quote_title":  self.quote_title,
            "items_total":  self.items_total,
            "items_ok":     self.items_ok,
            "items_failed": self.items_failed,
            "errors":       self.errors,
            "skipped":      self.skipped,
            "skip_reason":  self.skip_reason,
            "success":      self.success,
            "started_at":   self.started_at.isoformat(),
            "finished_at":  self.finished_at.isoformat() if self.finished_at else None,
        }


class Migrator:
    """
    Orquestra a migração de quotes do Jobber para o budget do JobTread.

    Uso básico:
        migrator = Migrator()

        # Migrar um job específico
        result = migrator.migrate_job(
            jobber_quote_id = "57649446",
            jt_job_id       = "22PVxgFHbqdU",
            override_cost_type = "Labor"  # opcional
        )

        # Migrar uma lista de jobs
        results = migrator.migrate_batch([
            {"jobber_quote_id": "57649446", "jt_job_id": "22PVxgFHbqdU"},
            {"jobber_quote_id": "57674580", "jt_job_id": "22PW2eZiNRyH", "cost_type": "Labor"},
        ])
    """

    def __init__(self, dry_run: bool = False, throttle: float = 0.3):
        """
        dry_run: se True, exibe o preview mas NÃO insere nada no JobTread
        throttle: intervalo em segundos entre chamadas à API (evitar rate limit)
        """
        self.dry_run  = dry_run
        self.throttle = throttle
        self.jobber   = JobberClient()
        self.jt       = JobTreadClient()
        print(f"  [Migrator] Inicializado {'(DRY RUN)' if dry_run else '(LIVE)'}")

    # ── Migração de job único ─────────────────────────────────────────────────

    def migrate_job(
        self,
        jobber_quote_id: str,
        jt_job_id: str,
        override_cost_type: str = None,
        override_cost_code: str = None,
        skip_existing: bool = True,
    ) -> MigrationResult:
        """
        Migra um único quote do Jobber para o budget de um job no JobTread.

        Parâmetros:
            jobber_quote_id:    ID numérico do quote no Jobber (ex: "57649446")
            jt_job_id:          ID do job no JobTread (ex: "22PVxgFHbqdU")
            override_cost_type: força costType para todos os itens ("Labor", "Materials", etc.)
            skip_existing:      se True, pula jobs que já têm cost items
        """
        result = MigrationResult(jobber_quote_id, jt_job_id)
        self._log(f"\n{'═'*70}")
        self._log(f"Migrando quote #{jobber_quote_id} → JT job {jt_job_id}")
        self._log(f"{'═'*70}")

        try:
            # 1. Buscar quote no Jobber
            self._log(f"  [1/4] Buscando quote #{jobber_quote_id} no Jobber...")
            quote = self.jobber.get_quote(jobber_quote_id)

            if not quote:
                result.skipped    = True
                result.skip_reason = f"Quote #{jobber_quote_id} não encontrado no Jobber"
                self._log(f"  ⚠ {result.skip_reason}")
                return result

            result.quote_title = quote.get("title", "")
            line_items = quote.get("lineItems", {}).get("nodes", [])
            self._log(f"  ✓ Quote encontrado: '{result.quote_title}' ({len(line_items)} itens)")

            # 2. Verificar job no JobTread
            self._log(f"  [2/4] Verificando job {jt_job_id} no JobTread...")
            jt_job = self.jt.get_job(jt_job_id)

            if not jt_job:
                result.skipped    = True
                result.skip_reason = f"Job {jt_job_id} não encontrado no JobTread"
                self._log(f"  ⚠ {result.skip_reason}")
                return result

            existing_items = jt_job.get("costItems", {}).get("nodes", [])
            # Filtrar apenas itens que não são do Preconstruction group
            non_pre_items = [i for i in existing_items
                             if i.get("name") not in ["Inspection and evaluation labor", "Final inspection"]]

            if skip_existing and non_pre_items:
                result.skipped    = True
                result.skip_reason = f"Job já possui {len(non_pre_items)} cost item(s) — pulando"
                self._log(f"  ⚠ {result.skip_reason}")
                return result

            self._log(f"  ✓ Job encontrado: '{jt_job.get('name', '')}' ({len(existing_items)} itens existentes)")

            # 3. Mapear line items
            self._log(f"  [3/4] Mapeando {len(line_items)} itens...")
            mapped_items = map_quote(quote, override_cost_type=override_cost_type, override_cost_code=override_cost_code)
            result.items_total = len(mapped_items)

            # Preview
            print(preview_mapping(quote, override_cost_type, override_cost_code))

            if self.dry_run:
                self._log(f"\n  [DRY RUN] Nenhum item foi inserido.")
                result.finished_at = datetime.now()
                return result

            # 4. Inserir itens no JobTread
            self._log(f"  [4/4] Inserindo {len(mapped_items)} itens no JobTread...")
            for i, item in enumerate(mapped_items, 1):
                try:
                    self.jt.create_cost_item(jt_job_id, item)
                    self._log(f"    ✓ [{i}/{len(mapped_items)}] {item['name'][:50]} "
                              f"(qty: {item['quantity']}, ${item['unitPrice']:.2f})")
                    result.items_ok += 1
                except Exception as e:
                    err_msg = f"Erro em '{item['name']}': {e}"
                    self._log(f"    ✗ [{i}/{len(mapped_items)}] {err_msg}")
                    result.errors.append(err_msg)
                    result.items_failed += 1

                time.sleep(self.throttle)

            status = "✅ SUCESSO" if result.success else "⚠ PARCIAL"
            self._log(f"\n  {status}: {result.items_ok} ok, {result.items_failed} erros")

        except Exception as e:
            result.errors.append(str(e))
            self._log(f"  ❌ ERRO CRÍTICO: {e}")

        finally:
            result.finished_at = datetime.now()
            self._save_log(result)

        return result

    # ── Migração em lote ──────────────────────────────────────────────────────

    def migrate_batch(self, jobs: list) -> list:
        """
        Migra uma lista de jobs.

        jobs: lista de dicts com keys:
            - jobber_quote_id (obrigatório)
            - jt_job_id       (obrigatório)
            - cost_type       (opcional — override)
            - skip_existing   (opcional — default True)

        Retorna lista de MigrationResult.
        """
        results  = []
        total    = len(jobs)
        ok       = 0
        failed   = 0
        skipped  = 0

        self._log(f"\n{'═'*70}")
        self._log(f"BATCH MIGRATION — {total} job(s)")
        self._log(f"{'═'*70}")

        for idx, job in enumerate(jobs, 1):
            self._log(f"\n[{idx}/{total}]")
            result = self.migrate_job(
                jobber_quote_id    = str(job["jobber_quote_id"]),
                jt_job_id          = str(job["jt_job_id"]),
                override_cost_type = job.get("cost_type"),
                skip_existing      = job.get("skip_existing", True),
            )
            results.append(result)

            if result.skipped:
                skipped += 1
            elif result.success:
                ok += 1
            else:
                failed += 1

        self._log(f"\n{'═'*70}")
        self._log(f"RESULTADO FINAL: {ok} ok | {failed} erros | {skipped} pulados")
        self._log(f"{'═'*70}\n")

        self._save_batch_report(results)
        return results

    # ── Utilitários ───────────────────────────────────────────────────────────

    def preview(self, jobber_quote_id: str, override_cost_type: str = None):
        """Exibe o preview de mapeamento de um quote sem inserir nada."""
        quote = self.jobber.get_quote(jobber_quote_id)
        if not quote:
            print(f"Quote #{jobber_quote_id} não encontrado.")
            return
        print(preview_mapping(quote, override_cost_type))

    def _log(self, msg: str):
        print(msg)

    def _save_log(self, result: MigrationResult):
        """Salva o log de uma migração em JSON."""
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = LOG_DIR / f"migration_{result.quote_id}_{ts}.json"
        path.write_text(json.dumps(result.to_dict(), indent=2))

    def _save_batch_report(self, results: list):
        """Salva o relatório de um batch em JSON."""
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = LOG_DIR / f"batch_{ts}.json"
        path.write_text(json.dumps(
            [r.to_dict() for r in results], indent=2
        ))
        print(f"  [Log] Relatório salvo em {path}")
