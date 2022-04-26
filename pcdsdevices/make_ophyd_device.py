import re
import sys

from whatrecord import db


def recurse_record(d, record):
    """
    Recurse through a given record, supplied as a list of strings, and create
    nested dictionaries. This helps parse any structure within the db file to
    help make device sub-classes. This method acts upon a supplied dictionary.
    """
    k = record.pop(0)
    if len(record) > 0:
        if k not in d.keys():
            d[k] = dict()
        recurse_record(d[k], record)
    else:
        if 'components' not in d.keys():
            d['components'] = []
        d['components'].append(k)


def make_signal(suffix, lines):
    """
    Create a Cpt line with specified suffix. This line is added to a supplied
    list, used for storing components within a particular class.
    """
    s = "    {0} = Cpt(EpicsSignal, \':{1}\', kind=\'normal\')"
    lines.append(s.format(suffix.lower(), suffix))


def make_signal_wrbv(suffix, lines):
    """
    Create a Cpt line with RBV pv and separate write_PV. This line is added to
    a supplied list, used for storing components within a particular class.
    """
    s = ("    {0} = Cpt(EpicsSignal, \':{1}_RBV\', write_pv=\':{1}\', "
         "kind=\'normal\')")
    lines.append(s.format(suffix.lower(), suffix))


def make_class_name(pv):
    """
    Make a class name based on a given PV.
    """
    return '{}'.format(pv.title())


def make_class_line(name, lines):
    """
    Make the first line of a class definition, based on a given PV or name.
    Appends the generated line to a list of lines.
    """
    s = 'class {}(BaseInterface, Device):'.format(make_class_name(name))
    lines.append(s)


def make_cpt(name, lines):
    """
    Make a component line for a sub-class, based on the supplied name.
    Appends the generated line to a list of lines.
    """
    s = "    {0} = Cpt({1}, \':{2}\', kind=\'normal\')"
    lines.append(s.format(name.lower(), make_class_name(name), name))


def get_components(pv_list):
    """
    Separate PVs in a given list of PVs based on whether a corresponding
    '_RBV' PV exists for the PV in the list. This is used to sort out PVs
    that can utilize a separate 'write_pv' in the component declaration.
    """
    # PVs could potentially be classified in a more fine-grained way. For now
    # it's kept simple.
    cpts_w_rbv = []
    cpts_wo_rbv = []
    for pv in pv_list:
        if pv+'_RBV' in pv_list:
            cpts_w_rbv.append(pv)
        # in case we found the RBV pv first:
        elif '_RBV' in pv:
            if pv.removesuffix('_RBV') in pv_list:
                cpts_w_rbv.append(pv.removesuffix('_RBV'))
        else:
            cpts_wo_rbv.append(pv)
    pv_dict = {}
    # The above algorithm is simple, can result in duplicates. Use set() to
    # clean things up.
    pv_dict['w_rbv'] = sorted(set(cpts_w_rbv))
    pv_dict['wo_rbv'] = sorted(set(cpts_wo_rbv))
    return pv_dict


def make_class(name, d):
    """
    Generate the requisite code for a simple python class for interacting with
    a device. Takes a desired class name and a dictionary of dictionaries,
    created using recurse_record, to generate all components and sub-components
    for a class. Recurses the dictionary, building up sub-classes as needed.
    """
    class_lines = []
    sub_class_lines = []
    make_class_line(name, class_lines)
    lines = sorted(d.keys())
    for key in lines:
        if key != 'components':
            make_cpt(key, class_lines)
            sub_class_lines.append(make_class(key, d[key]))
            sub_class_lines.append('\n\n')
        else:
            dcpt = get_components(d[key])
            for cpt in dcpt['w_rbv']:
                make_signal_wrbv(cpt, class_lines)
            for cpt in dcpt['wo_rbv']:
                make_signal(cpt, class_lines)
            class_lines + ['\n\n']

    return flatten_list(sub_class_lines + class_lines)


def flatten_list(lofl):
    """
    Flatten a list of lists.
    """
    new_list = []
    for item in lofl:
        if type(item) == list:
            rl = flatten_list(item)
            new_list.extend(rl)
        else:
            new_list.append(item)
    return new_list


def print_class(class_lines):
    for line in class_lines:
        print(line)


def write_file(lines, name):
    with open(name, 'a') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "db",
        type=str,
        help="The EPICS db file that the Ophyd class is to be based on.",
    )

    parser.add_argument(
        "name",
        type=str,
        help="The name of the device class you would like to create.",
    )

    parser.add_argument(
        "-e",
        "--echo",
        action="store_true",
        help="Print the output rather than writing to file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="The output file path.",
    )

    args = parser.parse_args()

    database = db.Database.from_file(args.db)
    record_list = list(database.records.keys())

    d = {}
    for record in record_list:
        # Sanitize the record of macros
        record = re.sub(r'\:?\$?\(.*\)\:?', '', record)
        recurse_record(d, record.split(':'))

    class_lines = make_class(args.name, d)
    file_lines = []
    docstring = '\"\"\"\n{0} class generated from {1}.\n\"\"\"\n'
    file_lines.append(docstring.format(args.name, args.db))
    file_lines.append('from ophyd import Component as Cpt')
    file_lines.append('from ophyd import Device, EpicsSignal')
    file_lines.append('\nfrom .interface import BaseInterface\n\n')
    file_lines = file_lines + class_lines

    if args.echo:
        print_class(file_lines)
        sys.exit(0)
    elif args.output:
        write_file(file_lines, args.output)
        print("\nDone!")
        print("Don't forget to run `black` and `flake8` on your new file!\n")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)
