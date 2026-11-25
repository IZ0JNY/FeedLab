from feedlab.filenames import clean


def test_default_when_empty():
    assert clean("", "feed_10GHz") == "feed_10GHz"
    assert clean("   ", "feed_10GHz") == "feed_10GHz"
    assert clean(None, "x") == "x"


def test_custom_name_kept_and_cleaned():
    assert clean("mio feed 24", "d") == "mio feed 24"
    assert clean("mio/feed:24?", "d") == "mio_feed_24_"
    assert clean("progetto.pdf", "d") == "progetto"
    assert clean("progetto.feedlab.json", "d") == "progetto"
    assert clean("con", "d") == "con_"
    assert clean("...", "d") == "d"
