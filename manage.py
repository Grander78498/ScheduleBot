#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    argv = sys.argv
    if argv[1] == "runbot":
        if len(argv) < 3 or argv[2] == "-d" or argv[2] == "--help" or argv[2] == "-h":
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_queue.settings')
        elif argv[2] == "-p":
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_queue.prod_settings')
        else:
            print('Малолетний дебил')
            exit(404)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
