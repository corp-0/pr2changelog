import pr2changelog as cl
from os import system

document = cl.document
changes = cl.change


def main():
    if not changes.change_lines:
        print("PR has no changes worthy enough to mention in changelog, skipping :)")
        system('echo "::set-env name=GENERATED_CHANGELOG::false"')
        return

    write_new_changes()


def write_new_changes():
    for new_change in changes.change_lines:
        print(f"Found new change: {new_change}")
        document.add_record(new_change)
        system('echo "::set-env name=GENERATED_CHANGELOG::true"')


if __name__ == "__main__":
    main()
