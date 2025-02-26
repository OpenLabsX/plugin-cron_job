import os
import pytest
import testinfra.utils.ansible_runner  # type: ignore
from testinfra.host import Host  # type: ignore
from time import sleep

# Get the host(s) provided by Molecule’s inventory.
testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ["MOLECULE_INVENTORY_FILE"]
).get_hosts("all")


def test_cron_job_exists(host: Host):
    # If the cron job is installed for the current user:
    cron_output = host.check_output("crontab -l")
    assert "* * * * * ls / > /tmp/output.txt" in cron_output


def test_cronjob_output_file(host: Host) -> None:
    # Check that /tmp/output.txt exists
    checks = 0
    max_checks_one_min = 12  # 60 / 5 = 12
    while checks <= max_checks_one_min:
        output_file = host.file("/tmp/output.txt")
        checks += 1

        # Poll for file to be created
        if not output_file.exists:
            sleep(5)
            continue

        assert output_file.exists, "/tmp/output.txt does not exist"
        break

    if checks > max_checks_one_min:
        pytest.fail(reason="Cron job output file not created within one minute.")

    # Check that the file is not empty
    assert output_file.size > 0, "/tmp/output.txt is empty"

    # Get the expected output by running 'ls /'
    expected_output = host.check_output("ls /").strip()

    # Read the content of /tmp/output.txt and remove extra whitespace
    file_contents = output_file.content_string.strip()

    # Validate that the file content matches the expected 'ls /' output.
    assert (
        expected_output == file_contents
    ), f"Expected output:\n{expected_output}\n\nGot:\n{file_contents}"
