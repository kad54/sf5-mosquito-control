"""Run the combined-centrality comparison supporting the SF5 coursework report."""

if __name__ == "__main__":
    if __package__:
        from .experiment import main
    else:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from dengue_simulation.experiment import main
    raise SystemExit(main())
