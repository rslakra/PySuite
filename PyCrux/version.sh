#!/usr/bin/env bash
# Turns a number (normally the commit count) into a MAJOR.MINOR.PATCH version string.
#
#   ./version.sh "$(git rev-list --count HEAD)"
#
# Prints only the version, so it can be used in scripts: V=$(./version.sh 42)
#
# Rules (N is the number you pass in):
#
#   N < 10         0.0.N        7    -> 0.0.7
#   N < 100        0.1.(N-10)   10   -> 0.1.0     42 -> 0.1.32     99 -> 0.1.89
#   N >= 100       D.X.Y        where, with L = the number of digits in N:
#                                 D (major) = L - 2
#                                 X (minor) = (N - 10^(L-1)) / 100   (whole number)
#                                 Y (patch) = N mod 100
#
#   100  -> 1.0.0     101  -> 1.0.1     199  -> 1.0.99    200  -> 1.1.0     999  -> 1.8.99
#   1000 -> 2.0.0     1234 -> 2.2.34    9999 -> 2.89.99   10000 -> 3.0.0
#
# A bigger N always gives a bigger version, and no two Ns give the same one. PyPI and TestPyPI refuse a
# re-upload of a version that was already published, so that's what a release needs.
# Each range starts at .0 (10 -> 0.1.0, 100 -> 1.0.0, 1000 -> 2.0.0), and the patch part is always 0-99.
# Pure bash and integer arithmetic: works with the bash 3.2 that ships with macOS.

set -euo pipefail

usage() {
  echo "Usage: ${0##*/} <number>" >&2
  echo "  <number>  a non-negative whole number, e.g. \$(git rev-list --count HEAD)" >&2
  echo "  Prints MAJOR.MINOR.PATCH, e.g. 7 -> 0.0.7, 10 -> 0.1.0, 101 -> 1.0.1" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

case "$1" in
  -h | --help)
    usage
    exit 0
    ;;
esac

input="$1"

if [[ ! "$input" =~ ^[0-9]+$ ]]; then
  echo "${0##*/}: '$input' is not a non-negative whole number" >&2
  usage
  exit 2
fi

# Drop leading zeros (so "007" isn't read as octal), and keep it inside 64-bit integer range.
stripped="${input#"${input%%[!0]*}"}"
stripped="${stripped:-0}"
if [[ ${#stripped} -gt 18 ]]; then
  echo "${0##*/}: '$input' is too large" >&2
  exit 2
fi
n=$((10#$stripped))

if ((n < 10)); then
  echo "0.0.$n"
elif ((n < 100)); then
  echo "0.1.$((n - 10))"
else
  digits=${#n}
  first=1 # 10^(digits-1): the smallest number with that many digits
  for ((i = 1; i < digits; i++)); do
    first=$((first * 10))
  done
  echo "$((digits - 2)).$(((n - first) / 100)).$((n % 100))"
fi
