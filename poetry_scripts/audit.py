from ossaudit import audit as oaudit
from ossaudit import packages

id_ignorelist = {
    "sonatype-2020-0201",
    "CVE-2019-20478",  # only triggered via improper use of library
    "sonatype-2021-0025",  # we know pickle is unsafe
    "CVE-2020-13091",  # we know pickle is unsafe
    "CVE-2019-12760",  # we still know pickle is unsafe
}
package_ignorelist = {
    "pywin32",  # we never run on windows
    "py"
}


def audit():
    deps = open("requirements.txt")
    pkgs = packages.get_from_files([deps])

    results = oaudit.components(pkgs)
    any_high = False
    for vuln in results:
        if vuln.name in package_ignorelist:
            continue
        if vuln.id in id_ignorelist:
            continue
        if vuln.cvss_score > 7.0:
            any_high = True

        print(f"{vuln.name},{vuln.version},{vuln.id},{vuln.cve},{vuln.cvss_score}")

    if any_high:
        exit(1)

    exit(0)
