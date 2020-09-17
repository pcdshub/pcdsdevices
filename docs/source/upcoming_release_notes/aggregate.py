import collections
import pathlib


def parse(text: str) -> dict:
    results = collections.OrderedDict()
    category = None
    lines = list(text.splitlines())

    for idx, (line, next_line) in enumerate(zip(lines, lines[1:] + ['']), 1):
        if not line.strip():
            ...
        elif set(next_line.strip()) == {'-'}:
            category = line.strip()
        elif set(line.strip()) == {'-'}:
            ...
        elif category is not None:
            if line.strip() != '- N/A':
                if category not in results:
                    results[category] = []
                results[category].append(line)
        elif idx > 2 and category is not None:
            raise ValueError(
                f'Malformed RST? Line outside of category: '
                f'line={idx} {line!r}'
            )

        previous_line = line

    return results


def aggregate() -> dict:
    information = {
        'API Changes': [],
        'Features': [],
        'Device Updates': [],
        'New Devices': [],
        'Bugfixes': [],
        'Maintenance': [],
        'Contributors': [],
    }

    skip = {'template-full.rst', 'template-short.rst'}

    for fn in sorted(pathlib.Path('.').glob('*.rst')):
        if fn.name in skip:
            continue

        with open(fn, 'rt') as f:
            raw = f.read()

        try:
            for category, info in parse(raw).items():
                if category not in information:
                    information[category] = []

                information[category].extend(info)
        except Exception:
            print('Failed on', fn)
            raise
    return information


for category, info in aggregate().items():
    print()
    print(category)
    print('-' * len(category))
    if category == 'Contributors':
        info = list(sorted(set(info)))

    for line in info:
        print(line)
