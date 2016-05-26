#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""io-touchpad application.

This application will learn to associate symbols you draw on your touchpad
with certain actions you bound to those symbols.

Your finger's absolute position is fetched using a library called touchpadlib
which is based on evtest (version 1.32).
"""

import argparse
import queue
import sys

from terminationhandler import terminationhandler
from threads import application
from threads import listener
from classifier import classifier as classifier_module

MIN_TRAINING_SIZE = 5

ACTIVATE_SUBCOMMAND = 'activate'
ADD_SUBCOMMAND = 'add'
DEACTIVATE_SUBCOMMAND = 'deactivate'
DELETE_SUBCOMMAND = 'delete'
LIST_SUBCOMMAND = 'list'
MODIFY_SUBCOMMAND = 'modify'
REPEAT_SUBCOMMAND = 'repeat'
RUN_SUBCOMMAND = 'run'
RUN_USER_MODE = 'user'
RUN_32_MODE = '32'
RUN_64_MODE = '64'


def _get_configured_parser():
    """Configure the commandline arguments parser."""
    description = 'Teaching your touchpad magic tricks since 2016.'
    parser = argparse.ArgumentParser(add_help=True, description=description)

    subparsers = parser.add_subparsers(metavar='SUBCOMMAND', dest='subcommand',
                                       help='available subcommands; run '
                                       'SUBCOMMAND -h to show help for '
                                       'the SUBCOMMAND you are interested in')
    subparsers.required = True  # Require SUBCOMMAND to be specified.

    # The activate subcommand section.
    subparser = subparsers.add_parser(ACTIVATE_SUBCOMMAND,
                                      help='activate selected symbols to be '
                                      'recognisable by the app')
    group = subparser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--all', dest='symbols', action='store_const',
                       const=[], help='activate all the existing symbols')
    group.add_argument('-s', '--select', dest='symbols', nargs="+",
                       help='activate all the selected symbols')

    # The add subcommand section.
    subparser = subparsers.add_parser(ADD_SUBCOMMAND, help='undertake a '
                                      'learning session in order to add '
                                      'a new symbol')
    subparser.add_argument(dest='training_size', metavar='SIZE',
                           help='you will be asked to draw '
                           'a symbol SIZE times; SIZE should be at '
                           'least {0}'.format(MIN_TRAINING_SIZE), type=int)
    subparser.add_argument(dest='symbol_name', metavar='SYMBOL',
                           help='the name of the symbol you want the app to '
                           'learn during the learning session')
    subparser.add_argument(dest='shell_command', metavar='COMMAND',
                           help='the shell command to be triggered when the '
                           'symbol is drawn; for e.g. "touch"')
    subparser.add_argument(dest='shell_command_arguments', metavar='ARGUMENTS',
                           help='the arguments for the shell command to be '
                           'triggered when the symbol is drawn; for '
                           'e.g. "/tmp/touched_file"')

    # The deactivate subcommand section.
    subparser = subparsers.add_parser(DEACTIVATE_SUBCOMMAND, help='deactivate '
                                      'existing symbols; the selected symbols '
                                      'will be not be recognised by the app; '
                                      'it is be possible to rectivate any of '
                                      'those symbols in the future')
    group = subparser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--all', dest='symbols', action='store_const',
                       const=[], help='deactivate all symbols')
    group.add_argument('-s', '--select', dest='symbols', nargs="+",
                       help='deactivate all the symbols from the list')

    # The delete subcommand section.
    subparser = subparsers.add_parser(DELETE_SUBCOMMAND, help='delete '
                                      'selected symbols; the selected symbols '
                                      'will be removed and lost forever')
    group = subparser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a', '--all', dest='symbols', action='store_const',
                       const=[], help='delete all the existing symbols')
    group.add_argument('-s', '--select', dest='symbols', nargs="+",
                       help='delete all the symbols from the list')

    # The list subcommand section.
    subparsers.add_parser(LIST_SUBCOMMAND, help='list all the available '
                          'symbols (both activated ' 'and deactivated)')

    # The modify subcommand section.
    subparser = subparsers.add_parser(MODIFY_SUBCOMMAND, help='modify the '
                                          'command assigned to a symbol')
    subparser.add_argument(dest='symbol_name', default=None,
                           metavar='SYMBOL', help='the name of the symbol '
                           'the user wants to modify')
    subparser.add_argument(dest='new_shell_command', default=None,
                           metavar='COMMAND', help='the new shell command '
                           'to be triggered when the symbol is drawn')

    # The repeat subcommand section.
    subparser = subparsers.add_parser(REPEAT_SUBCOMMAND, help='repeat the '
                                     'learning process of all the'
                                     'symbols; use the --symbol option '
                                     'to repeat the process for only one '
                                     'symbol')
    subparser.add_argument('-s', '--symbol', dest='symbol_name',
                               default=None, metavar='SYMBOL', help='repeat '
                               'the learning process for the SYMBOL only; '
                               'if this option is not provided then '
                               'the learning process will be '
                               'repeated for each symbol known to the app')

    # The run subcommand section.
    subparser = subparsers.add_parser(RUN_SUBCOMMAND, help='run the app '
                                       'using hardcoded or user-defined '
                                       'symbols')
    subparser.add_argument(dest='run_mode', metavar='MODE',
                            choices={RUN_32_MODE, RUN_64_MODE, RUN_USER_MODE},
                            help='set the mode you would like to run the '
                            'app in; use <32> for 32-bit machines, <64> for '
                            '64-bit machines and <user> to use user-defined '
                            'symbols')

    return parser


def _start_threads(learning_mode=None, training_size=None, system_bitness=None,
                   symbol_name=None):
    """Wrap the threads launching.

    Args:
        learning_mode (bool): The variable which stores the information if
            the app would like to enter the learning mode or not.
        training_size (int): The number of the learning samples of the symbol
            that the user is asked to draw.
        system_bitness (int): The bitness of the system. The only legal values
            are {None, 32, 64}. If the value is 32 or 64 then set of hardcoded
            symbols (with respect to the provided bitness) will be
            recogniezed instead of the user defined symbols.
        symbol_name (str): The name of the symbol provided by the user with
            a command line option.
    """
    thread_queue = queue.Queue()

    # Run both threads.
    listener.start(thread_queue)
    application.application_thread(thread_queue, learning_mode, training_size,
                                   system_bitness, symbol_name)


def main():
    """The main function."""
    terminationhandler.setup()

    parser = _get_configured_parser()
    args = parser.parse_args()

    if args.subcommand == ACTIVATE_SUBCOMMAND:
        print('app.py: warning: the command line argument "activate" '
              'has not been implemented yet', file=sys.stderr)
        print('app.py: notice: the list of selected symbols: '
              '{0}'.format(args.symbols), file=sys.stderr)
        sys.exit(0)
    elif args.subcommand == ADD_SUBCOMMAND:
        print('The symbol name is ' + args.symbol_name + '.')
        if args.training_size < MIN_TRAINING_SIZE:
            print('app.py: error: the training size should be at least %d'
                  % (MIN_TRAINING_SIZE), file=sys.stderr)
            sys.exit(1)
        _start_threads(learning_mode=True, symbol_name=args.symbol_name,
                       training_size=args.training_size)
    elif args.subcommand == DEACTIVATE_SUBCOMMAND:
        print('app.py: warning: the command line argument "deactivate" '
              'has not been implemented yet', file=sys.stderr)
        print('app.py: notice: the list of selected symbols: '
              '{0}'.format(args.symbols), file=sys.stderr)
        sys.exit(0)
    elif args.subcommand == DELETE_SUBCOMMAND:
        print('app.py: warning: the command line argument "delete" '
              'has not been implemented yet', file=sys.stderr)
        print('app.py: notice: the list of selected symbols: '
              '{0}'.format(args.symbols), file=sys.stderr)
        sys.exit(0)
    elif args.subcommand == LIST_SUBCOMMAND:
        print('app.py: warning: the command line argument "list" '
              'has not been implemented yet', file=sys.stderr)
        sys.exit(0)
    elif args.subcommand == MODIFY_SUBCOMMAND:
        print('app.py: warning: the command line argument "modify SYMBOL '
              'COMMAND" has not been implemented yet', file=sys.stderr)
        sys.exit(0)
    elif args.subcommand == REPEAT_SUBCOMMAND:
        print('Repeating the classification within the learning process.')
        classifier = classifier_module.Classifier(True)
        classifier.learn(True, args.symbol_name)
        sys.exit(0)
    elif args.subcommand == RUN_SUBCOMMAND:
        try:
            system_bitness = int(args.run_mode)
        except ValueError:
            system_bitness = None
        finally:
            _start_threads(system_bitness=system_bitness)

main()
