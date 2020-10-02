import pr2changelog as cl
from os import system

changes = cl.change
if changes.change_lines:
    document = cl.document


def main():
    if not changes.change_lines:
        print("PR has no changes worthy enough to mention in changelog, skipping :)")
        system('echo "::set-output name=generated_changelog::0"')
        return

    write_new_changes()
    system('echo "::set-output name=generated_changelog::1"')


def write_new_changes():
    for new_change in changes.change_lines:
        print(f"Found new change: {new_change}")

    for formatted_change in changes.get_changes():
        document.add_record(formatted_change)


if __name__ == "__main__":
    main()
#0