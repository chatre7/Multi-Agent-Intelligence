"""
Skill Management CLI.
"""

import argparse
import sys
from pathlib import Path

# Add backend to sys.path to allow running this script directly
backend_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(backend_root))

from src.infrastructure.config.skill_marketplace import SkillMarketplace
from src.infrastructure.config.skill_loader import SkillLoader
from src.infrastructure.config.skill_importer import SkillImporter


def main():
    parser = argparse.ArgumentParser(description="Agent Skills CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list
    subparsers.add_parser("list", help="List available skills in registry")

    # installed
    subparsers.add_parser("installed", help="List installed skills")

    # search
    search_parser = subparsers.add_parser("search", help="Search skills")
    search_parser.add_argument("query", help="Search query")

    # install
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("skill_id", help="Skill ID")
    install_parser.add_argument("--version", default="latest", help="Version to install")
    install_parser.add_argument("--force", action="store_true", help="Force overwrite")

    # import
    import_parser = subparsers.add_parser("import", help="Import skill from Git")
    import_parser.add_argument("url", help="Git Repository URL")
    import_parser.add_argument("--branch", help="Git branch/tag")

    args = parser.parse_args()

    # Config (defaults)
    # in real app, these should come from config file/env
    registry_url = "https://raw.githubusercontent.com/eternal-agent-recall/skill-registry/main/index.json"
    local_skills_dir = backend_root / "configs" / "skills"
    
    marketplace = SkillMarketplace(registry_url, local_skills_dir)
    loader = SkillLoader(local_skills_dir)

    if args.command == "list":
        try:
            skills = marketplace.list_available_skills()
            print(f"Available Skills ({len(skills)}):")
            for skill in skills:
                print(f"  - {skill.id} ({skill.latest_version}): {skill.description}")
        except Exception as e:
            print(f"Error listing skills: {e}")

    elif args.command == "installed":
        skills = loader.load_all_skills()
        print(f"Installed Skills ({len(skills)}):")
        for skill in skills:
            print(f"  - {skill.id} @ {skill.version}")

    elif args.command == "search":
        try:
            results = marketplace.search_skills(args.query)
            print(f"Search Results ({len(results)}):")
            for skill in results:
                print(f"  - {skill.id} ({skill.latest_version}): {skill.description} [Tags: {', '.join(skill.tags)}]")
        except Exception as e:
            print(f"Error searching: {e}")

    elif args.command == "install":
        print(f"Installing {args.skill_id}@{args.version}...")
        try:
            skill = marketplace.install_skill(args.skill_id, args.version, args.force)
            print(f"Successfully installed {skill.id}@{skill.version}")
        except Exception as e:
            print(f"Installation failed: {e}")
            sys.exit(1)

    elif args.command == "import":
        importer = SkillImporter(local_skills_dir)
        print(f"Importing from {args.url}...")
        try:
            skill = importer.import_from_git(args.url, args.branch)
            print(f"Successfully imported {skill.id}@{skill.version}")
        except Exception as e:
            print(f"Import failed: {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
