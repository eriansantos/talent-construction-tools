#!/usr/bin/env python3
# =============================================================================
# migrate.py — CLI de migração Jobber → JobTread
# Talent Construction
# =============================================================================
#
# USO:
#
#   # Migrar um job específico
#   python migrate.py run --quote 57649446 --job 22PVxgFHbqdU
#
#   # Migrar com costType forçado
#   python migrate.py run --quote 57674580 --job 22PW2eZiNRyH --type Labor
#
#   # Dry run (preview sem inserir)
#   python migrate.py run --quote 57649446 --job 22PVxgFHbqdU --dry-run
#
#   # Preview de mapeamento
#   python migrate.py preview --quote 57649446
#
#   # Migrar uma lista de jobs (batch) via arquivo JSON
#   python migrate.py batch --file jobs.json
#
#   # Migrar uma lista de jobs inline
#   python migrate.py batch \
#     --pairs "57649446:22PVxgFHbqdU,57674580:22PW2eZiNRyH" \
#     --type Labor
#
# =============================================================================

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.migrator import Migrator


def cmd_run(args):
    migrator = Migrator(dry_run=args.dry_run)
    result   = migrator.migrate_job(
        jobber_quote_id    = args.quote,
        jt_job_id          = args.job,
        override_cost_type = args.type,
        override_cost_code = args.code,
        skip_existing      = not args.force,
    )
    if result.success:
        print(f"\n✅ Migração concluída: {result.items_ok} itens inseridos.")
    elif result.skipped:
        print(f"\n⚠ Pulado: {result.skip_reason}")
    else:
        print(f"\n❌ Falha: {result.items_failed} erros.")
        for err in result.errors:
            print(f"   - {err}")
    return 0 if result.success or result.skipped else 1


def cmd_preview(args):
    migrator = Migrator(dry_run=True)
    migrator.preview(args.quote, override_cost_type=args.type)
    return 0


def cmd_batch(args):
    jobs = []

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"❌ Arquivo não encontrado: {args.file}")
            return 1
        jobs = json.loads(path.read_text())

    elif args.pairs:
        for pair in args.pairs.split(","):
            parts = pair.strip().split(":")
            if len(parts) != 2:
                print(f"❌ Par inválido: '{pair}' — use formato quote_id:jt_job_id")
                return 1
            jobs.append({
                "jobber_quote_id": parts[0].strip(),
                "jt_job_id":       parts[1].strip(),
                "cost_type":       args.type,
            })

    if not jobs:
        print("❌ Nenhum job fornecido. Use --file ou --pairs.")
        return 1

    migrator = Migrator(dry_run=args.dry_run)
    results  = migrator.migrate_batch(jobs)

    ok      = sum(1 for r in results if r.success)
    failed  = sum(1 for r in results if not r.success and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)

    print(f"\n{'═'*50}")
    print(f"BATCH FINALIZADO: {ok} ok | {failed} erros | {skipped} pulados")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Talent Construction — Migração Jobber → JobTread"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── run ──────────────────────────────────────────────────────────────────
    run_parser = subparsers.add_parser("run", help="Migrar um job específico")
    run_parser.add_argument("--quote",   required=True, help="ID do quote no Jobber")
    run_parser.add_argument("--job",     required=True, help="ID do job no JobTread")
    run_parser.add_argument("--type",    default=None,  help="Forçar costType (ex: Labor, Materials)")
    run_parser.add_argument("--code",    default=None,  help="Forçar costCode (ex: Miscellaneous, Tiling)")
    run_parser.add_argument("--dry-run", action="store_true", help="Preview sem inserir")
    run_parser.add_argument("--force",   action="store_true", help="Inserir mesmo se já houver itens")

    # ── preview ───────────────────────────────────────────────────────────────
    prev_parser = subparsers.add_parser("preview", help="Preview de mapeamento de um quote")
    prev_parser.add_argument("--quote", required=True, help="ID do quote no Jobber")
    prev_parser.add_argument("--type",  default=None,  help="Forçar costType")

    # ── batch ─────────────────────────────────────────────────────────────────
    batch_parser = subparsers.add_parser("batch", help="Migrar múltiplos jobs")
    batch_parser.add_argument("--file",    default=None, help="Arquivo JSON com lista de jobs")
    batch_parser.add_argument("--pairs",   default=None, help="Pares quote_id:jt_job_id separados por vírgula")
    batch_parser.add_argument("--type",    default=None, help="Forçar costType para todos")
    batch_parser.add_argument("--dry-run", action="store_true", help="Preview sem inserir")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "preview":
        sys.exit(cmd_preview(args))
    elif args.command == "batch":
        sys.exit(cmd_batch(args))


if __name__ == "__main__":
    main()
