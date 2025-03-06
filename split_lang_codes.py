# a lot our 041 language codes are all stuffed into one $a subfield
# instead of a separate $a for each language code
# 041 1_ $aengjpn -> 041 1_ $aeng$ajpn
from pathlib import Path
import sys
from typing import Any, Literal, Set
import unittest

import click
from pymarc import Indicators, Record, Subfield, MARCReader, MARCWriter, Field

# List of ISO 639.2 language codes
# https://www.loc.gov/standards/iso639-2/php/code_list.php
codes: list[str] = [
    "aar",
    "abk",
    "ace",
    "ach",
    "ada",
    "ady",
    "afa",
    "afh",
    "afr",
    "ain",
    "aka",
    "akk",
    "alb",
    "ale",
    "alg",
    "alt",
    "amh",
    "ang",
    "anp",
    "apa",
    "ara",
    "arc",
    "arg",
    "arm",
    "arn",
    "arp",
    "art",
    "arw",
    "asm",
    "ast",
    "ath",
    "aus",
    "ava",
    "ave",
    "awa",
    "aym",
    "aze",
    "bad",
    "bai",
    "bak",
    "bal",
    "bam",
    "ban",
    "baq",
    "bas",
    "bat",
    "bej",
    "bel",
    "bem",
    "ben",
    "ber",
    "bho",
    "bih",
    "bik",
    "bin",
    "bis",
    "bla",
    "bnt",
    "tib",
    "bos",
    "bra",
    "bre",
    "btk",
    "bua",
    "bug",
    "bul",
    "bur",
    "byn",
    "cad",
    "cai",
    "car",
    "cat",
    "cau",
    "ceb",
    "cel",
    "cze",
    "cha",
    "chb",
    "che",
    "chg",
    "chi",
    "chk",
    "chm",
    "chn",
    "cho",
    "chp",
    "chr",
    "chu",
    "chv",
    "chy",
    "cmc",
    "cnr",
    "cop",
    "cor",
    "cos",
    "cpe",
    "cpf",
    "cpp",
    "cre",
    "crh",
    "crp",
    "csb",
    "cus",
    "wel",
    "cze",
    "dak",
    "dan",
    "dar",
    "day",
    "del",
    "den",
    "ger",
    "dgr",
    "din",
    "div",
    "doi",
    "dra",
    "dsb",
    "dua",
    "dum",
    "dut",
    "dyu",
    "dzo",
    "efi",
    "egy",
    "eka",
    "gre",
    "elx",
    "eng",
    "enm",
    "epo",
    "est",
    "baq",
    "ewe",
    "ewo",
    "fan",
    "fao",
    "per",
    "fat",
    "fij",
    "fil",
    "fin",
    "fiu",
    "fon",
    "fre",
    "fre",
    "frm",
    "fro",
    "frr",
    "frs",
    "fry",
    "ful",
    "fur",
    "gaa",
    "gay",
    "gba",
    "gem",
    "geo",
    "ger",
    "gez",
    "gil",
    "gla",
    "gle",
    "glg",
    "glv",
    "gmh",
    "goh",
    "gon",
    "gor",
    "got",
    "grb",
    "grc",
    "gre",
    "grn",
    "gsw",
    "guj",
    "gwi",
    "hai",
    "hat",
    "hau",
    "haw",
    "heb",
    "her",
    "hil",
    "him",
    "hin",
    "hit",
    "hmn",
    "hmo",
    "hrv",
    "hsb",
    "hun",
    "hup",
    "arm",
    "iba",
    "ibo",
    "ice",
    "ido",
    "iii",
    "ijo",
    "iku",
    "ile",
    "ilo",
    "ina",
    "inc",
    "ind",
    "ine",
    "inh",
    "ipk",
    "ira",
    "iro",
    "ice",
    "ita",
    "jav",
    "jbo",
    "jpn",
    "jpr",
    "jrb",
    "kaa",
    "kab",
    "kac",
    "kal",
    "kam",
    "kan",
    "kar",
    "kas",
    "geo",
    "kau",
    "kaw",
    "kaz",
    "kbd",
    "kha",
    "khi",
    "khm",
    "kho",
    "kik",
    "kin",
    "kir",
    "kmb",
    "kok",
    "kom",
    "kon",
    "kor",
    "kos",
    "kpe",
    "krc",
    "krl",
    "kro",
    "kru",
    "kua",
    "kum",
    "kur",
    "kut",
    "lad",
    "lah",
    "lam",
    "lao",
    "lat",
    "lav",
    "lez",
    "lim",
    "lin",
    "lit",
    "lol",
    "loz",
    "ltz",
    "lua",
    "lub",
    "lug",
    "lui",
    "lun",
    "luo",
    "lus",
    "mac",
    "mad",
    "mag",
    "mah",
    "mai",
    "mak",
    "mal",
    "man",
    "mao",
    "map",
    "mar",
    "mas",
    "may",
    "mdf",
    "mdr",
    "men",
    "mga",
    "mic",
    "min",
    "mis",
    "mac",
    "mkh",
    "mlg",
    "mlt",
    "mnc",
    "mni",
    "mno",
    "moh",
    "mon",
    "mos",
    "mao",
    "may",
    "mul",
    "mun",
    "mus",
    "mwl",
    "mwr",
    "bur",
    "myn",
    "myv",
    "nah",
    "nai",
    "nap",
    "nau",
    "nav",
    "nbl",
    "nde",
    "ndo",
    "nds",
    "nep",
    "new",
    "nia",
    "nic",
    "niu",
    "dut",
    "nno",
    "nob",
    "nog",
    "non",
    "nor",
    "nqo",
    "nso",
    "nub",
    "nwc",
    "nya",
    "nym",
    "nyn",
    "nyo",
    "nzi",
    "oci",
    "oji",
    "ori",
    "orm",
    "osa",
    "oss",
    "ota",
    "oto",
    "paa",
    "pag",
    "pal",
    "pam",
    "pan",
    "pap",
    "pau",
    "peo",
    "per",
    "phi",
    "phn",
    "pli",
    "pol",
    "pon",
    "por",
    "pra",
    "pro",
    "pus",
    "qaa",
    "que",
    "raj",
    "rap",
    "rar",
    "roa",
    "roh",
    "rom",
    "rum",
    "rum",
    "run",
    "rup",
    "rus",
    "sad",
    "sag",
    "sah",
    "sai",
    "sal",
    "sam",
    "san",
    "sas",
    "sat",
    "scn",
    "sco",
    "sel",
    "sem",
    "sga",
    "sgn",
    "shn",
    "sid",
    "sin",
    "sio",
    "sit",
    "sla",
    "slo",
    "slo",
    "slv",
    "sma",
    "sme",
    "smi",
    "smj",
    "smn",
    "smo",
    "sms",
    "sna",
    "snd",
    "snk",
    "sog",
    "som",
    "son",
    "sot",
    "spa",
    "alb",
    "srd",
    "srn",
    "srp",
    "srr",
    "ssa",
    "ssw",
    "suk",
    "sun",
    "sus",
    "sux",
    "swa",
    "swe",
    "syc",
    "syr",
    "tah",
    "tai",
    "tam",
    "tat",
    "tel",
    "tem",
    "ter",
    "tet",
    "tgk",
    "tgl",
    "tha",
    "tib",
    "tig",
    "tir",
    "tiv",
    "tkl",
    "tlh",
    "tli",
    "tmh",
    "tog",
    "ton",
    "tpi",
    "tsi",
    "tsn",
    "tso",
    "tuk",
    "tum",
    "tup",
    "tur",
    "tut",
    "tvl",
    "twi",
    "tyv",
    "udm",
    "uga",
    "uig",
    "ukr",
    "umb",
    "und",
    "urd",
    "uzb",
    "vai",
    "ven",
    "vie",
    "vol",
    "vot",
    "wak",
    "wal",
    "war",
    "was",
    "wel",
    "wen",
    "wln",
    "wol",
    "xal",
    "xho",
    "yao",
    "yap",
    "yid",
    "yor",
    "ypk",
    "zap",
    "zbl",
    "zen",
    "zgh",
    "zha",
    "chi",
    "znd",
    "zul",
    "zun",
    "zxx",
    "zza",
]


def sort_subfield_codes(code_list: list[str]) -> tuple[Set[str], Set[str]]:
    """Sort subfield codes into sets of invalid and valid ones"""
    invalid_codes: Set[str] = set()
    valid_codes: Set[str] = set()
    for code in code_list:
        if code not in codes:
            invalid_codes.add(code)
        else:
            valid_codes.add(code)
    return invalid_codes, valid_codes


def copy_non_a_subfields(original_field: Field, new_field: Field) -> None:
    """Copies non-$a subfields (e.g. $h original lang) from one field to another"""
    # We need to preserve other subfields when we reconstruct $a ones
    non_a_subfields: dict[str, list[Any]] = original_field.subfields_as_dict()
    if original_field.get("a"):
        non_a_subfields.pop("a")
    for letter in non_a_subfields.keys():
        for value in non_a_subfields[letter]:
            new_field.add_subfield(code=letter, value=value)


def split_lang_codes(record: Record, debug: bool = False) -> Record:
    """Split multiple language codes in 041 $a into separate subfields"""
    for field in record.get_fields("041"):
        # only process fields that use the MARC language codes
        if field.indicator2 == " ":
            if debug:
                click.echo(f"Processing field {field}")

            # sort subfields into categories
            invalid_codes, valid_codes = sort_subfield_codes(field.get_subfields("a"))

            if invalid_codes:
                if debug:
                    click.echo(f"Invalid subfield values: {invalid_codes}")

                for code in invalid_codes:
                    if len(code) % 3 == 0:
                        for i in range(0, len(code), 3):
                            # this step also fixes uppercase codes
                            split_code: str = code[i : i + 3].lower()
                            if split_code in codes:
                                valid_codes.add(split_code)
                            # we have a number of records using the wrong code for Japanese
                            elif split_code == "jap":
                                valid_codes.add("jpn")
                            elif split_code == "esk":
                                # NOTE: assumes language is Inuktitut & not another Inuit language
                                # like Iñupiaq (ipk). This is true for our collection though & Inuktitut
                                # is the most common. Note that `iku` also covers Inuinnaqtun.
                                # https://en.wikipedia.org/wiki/Eskaleut_languages#Internal_classification
                                valid_codes.add("iku")
                            else:
                                click.echo(
                                    f"Warning: unrecognized language code {split_code} after splitting {field} in record {record.title}. This code will be removed from the record.",
                                    err=True,
                                )
                    else:
                        click.echo(
                            f"Warning: length of language code {code} in {field} in record {record.title} is not divisible by 3 so we don't know how to split it into valid codes. It will be removed from the record.",
                            err=True,
                        )
                if len(valid_codes):
                    new_field: Field = Field(
                        tag="041",
                        indicators=field.indicators,
                        subfields=[
                            Subfield(code="a", value=code) for code in valid_codes
                        ],
                    )
                    copy_non_a_subfields(field, new_field)

                if debug:
                    click.echo(f"New field: {new_field}")

                record.remove_field(field)
                if "new_field" in locals():
                    record.add_ordered_field(new_field)

    return record


def make_041(subfields: list[tuple[str, str]]) -> Field:
    """Make a 041 field, helper functions for tests"""
    return Field(
        tag="041",
        indicators=Indicators("0", " "),
        subfields=[Subfield(code=c, value=v) for c, v in subfields],
    )


def make_record(subfields: list[tuple[str, str]]) -> Record:
    """Same as above except it returns a record with just a 041 field"""
    r = Record()
    r.add_field(make_041(subfields))
    return r


class SplitLangCodesTests(unittest.TestCase):
    def test_sort_subfield_codes(self) -> None:
        # 1 valid, 1 invalid
        i, v = sort_subfield_codes(["eng", "xxx"])
        assert "xxx" in i
        assert "eng" in v
        # 2 valid codes
        i, v = sort_subfield_codes(["eng", "jpn"])
        assert len(i) == 0
        assert "eng" in v
        assert "jpn" in v
        # 1 invalid
        i, v = sort_subfield_codes(["xxx"])
        assert "xxx" in i
        assert len(v) == 0
        # 1 invalid - too long
        i, v = sort_subfield_codes(["english"])
        assert "english" in i
        assert len(v) == 0
        # 2 invalid
        i, v = sort_subfield_codes(["english", "xxx"])
        assert "english" in i
        assert "xxx" in i
        assert len(v) == 0

    def test_copy_non_a_subfields(self) -> None:
        # no non-a subfields to copy
        f1: Field = make_041([("a", "eng")])
        f2: Field = make_041([("a", "eng")])
        copy_non_a_subfields(f1, f2)
        self.assertListEqual(
            f1.get_subfields("a", "b", "c"), f2.get_subfields("a", "b", "c")
        )

        # copy 1 h subfield
        f1: Field = make_041([("a", "eng"), ("h", "ger")])
        f2: Field = make_041([("a", "eng")])
        copy_non_a_subfields(f1, f2)
        self.assertListEqual(f1.get_subfields("h"), f2.get_subfields("h"))

        # copy 2 non-a subfields
        f1: Field = make_041([("b", "iku"), ("h", "ger")])
        f2: Field = make_041([("a", "eng")])
        copy_non_a_subfields(f1, f2)
        self.assertListEqual(f1.get_subfields("b"), f2.get_subfields("b"))
        self.assertListEqual(f1.get_subfields("h"), f2.get_subfields("h"))

    def test_split_lang_codes(self) -> None:
        # NOTE: all the type ignores are b/c Record.get(tag) can return None
        # but we assert that isinstance(Record.get(tag), Field) anyways.

        # valid record with one subfield, no changes
        r: Record = make_record([("a", "eng")])
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert r.get("041").get_subfields("a")[0] == "eng"  # type: ignore

        # valid record with two subfields
        r: Record = make_record([("a", "eng"), ("a", "fre")])
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert "eng" in r.get("041").get_subfields("a")  # type: ignore
        assert "fre" in r.get("041").get_subfields("a")  # type: ignore

        # invalid combined code is fixed
        r: Record = make_record([("a", "engspa")])
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert "eng" in r.get("041").get_subfields("a")  # type: ignore
        assert "spa" in r.get("041").get_subfields("a")  # type: ignore

        # invalid combined code is fixed alongside valid one
        r: Record = make_record([("a", "engspa"), ("a", "kor")])
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert "eng" in r.get("041").get_subfields("a")  # type: ignore
        assert "spa" in r.get("041").get_subfields("a")  # type: ignore
        assert "kor" in r.get("041").get_subfields("a")  # type: ignore

        # invalid code that can't be fixed is dropped
        r: Record = make_record([("a", "oijasidojaisd")])
        r = split_lang_codes(r)
        assert r.get("041") == None

        # valid code alongside invalid one that can't be fixed
        r: Record = make_record([("a", "oijasidojaisd"), ("a", "eng")])
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert len(r.get("041").get_subfields("a")) == 1  # type: ignore
        assert "eng" in r.get("041").get_subfields("a")  # type: ignore

        # convert esk -> iku, jap -> jpn
        r: Record = make_record([("a", "esk"), ("a", "jap")])
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert len(r.get("041").get_subfields("a")) == 2  # type: ignore
        assert "iku" in r.get("041").get_subfields("a")  # type: ignore
        assert "jpn" in r.get("041").get_subfields("a")  # type: ignore

        # skip field using non-MARC codes (2nd indicator is not null)
        r = Record()
        r.add_field(
            Field(
                tag="041",
                indicators=Indicators("1", "7"),
                subfields=[
                    Subfield(code="a", value="en"),
                    Subfield(code="2", value="iso639-1"),
                ],
            )
        )
        r = split_lang_codes(r)
        assert isinstance(r.get("041"), Field)
        assert len(r.get("041").get_subfields("a")) == 1  # type: ignore
        assert "en" in r.get("041").get_subfields("a")  # type: ignore


def run_tests(verbose: bool) -> Literal[0, 1]:
    loader = unittest.TestLoader()
    suite: unittest.TestSuite = loader.loadTestsFromTestCase(SplitLangCodesTests)
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 0)
    result: unittest.TextTestResult = runner.run(suite)

    # Return 0 for success, 1 for failures
    return 0 if result.wasSuccessful() else 1


@click.group()
@click.help_option("--help", "-h")
def cli():
    """Takes MARC 041 language subfields where multiple language codes are in a single $a subfield and splits them into separate subfields. Example: 041 1_ $a engjpn -> 041 1_ $a eng $a jpn (spaces added for readability)"""
    pass


@cli.command()
@click.help_option("--help", "-h")
@click.argument(
    "input",
    metavar="input.mrc",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.argument(
    "output",
    metavar="output.mrc",
    type=click.Path(dir_okay=False, writable=True),
    required=False,
)
@click.option("--debug", "-d", is_flag=True, help="Print changes, do not write to file")
def fix(input: Path, output: Path, debug: bool) -> None:
    """Fix input records"""
    with open(input, "rb") as input_fh:
        if output:
            writer = MARCWriter(open(output, "wb"))
        reader = MARCReader(input_fh)
        for record in reader:
            if record:
                new_record: Record = split_lang_codes(record, debug)
                if not debug and output:
                    writer.write(new_record)
        if output:
            writer.close()


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="more verbose test output")
def test(verbose: bool):
    """Run the test suite."""
    sys.exit(run_tests(verbose))


if __name__ == "__main__":
    cli()
