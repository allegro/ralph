#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2013 by Łukasz Langa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Choices - an enum implementation for Django forms and models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import partial
from textwrap import dedent

import six

unset = object()
gettext = unset
no_id_given = -255


class ChoicesEntry(int):
    global_id = 0

    def __new__(cls, *args, **kwargs):
        return super(ChoicesEntry, cls).__new__(cls, kwargs[str("id")])

    def __init__(self, description, id, name=None):
        self.raw = description
        self.global_id = ChoicesEntry.global_id
        self.name = name
        self.__extra__ = []
        ChoicesEntry.global_id += 1

    @property
    def desc(self):
        if not self.raw:
            return self.raw
        # gettext obscured that way so you can use choices in settings.py
        global gettext
        if gettext is unset:
            from django.utils.translation import gettext
        return gettext(self.raw)

    @property
    def id(self):
        return int(self)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value.strip("_") if value else value
        self.__raw_name = value

    def __unicode__(self, raw=False):
        """Always returns Unicode."""
        name = self.name
        if raw:
            name = "{!r}".format(name)
            if name[0] in "bru":
                name = name[2:-1]
            else:
                name = name[1:-1]
        return "<{}: {} (id: {})>".format(self.__class__.__name__, name, self.id)

    def __str__(self, raw=False):
        """Returns Unicode on Py3, bytes on Py2."""
        result = self.__unicode__(raw=raw)
        if six.PY2:
            result = result.encode("utf8")
        return result

    def __repr__(self):
        """Returns escaped Unicode on Py3, escaped bytes on Py2."""
        return self.__str__(raw=True)

    def extra(self, **other):
        """Enables adding custom attributes to choices at declaration time.
        For example::

            class Color(Choices):
                _ = Choices.Choice

                red = _("red").extra(html='#ff0000')
                green = _("green").extra(html='#00ff00')
                blue = _("blue").extra(html='#0000ff')

        Later on you can use the defined attribute directly::

            >>> Color.red.html
            '#ff0000'

        or with choices received using the getters::

            >>> Color.from_name(request.POST['color']).html
            '#00ff00'
        """
        for key, value in six.iteritems(other):
            self.__extra__.append(key)
            setattr(self, key, value)
        return self

    def __lshift__(self, other):
        """Deprecated: use choice.extra(arg=value)."""
        return self.extra(**other)


class ChoiceGroup(ChoicesEntry):
    """A group of choices."""

    def __new__(cls, *args, **kwargs):
        return super(ChoiceGroup, cls).__new__(cls, id=kwargs.get(str("id"), args[0]))

    def __init__(self, id, description=""):
        super(ChoiceGroup, self).__init__(description, id=id)
        self.choices = []


class Choice(ChoicesEntry):
    """A single choice."""

    def __new__(cls, *args, **kwargs):
        return super(Choice, cls).__new__(cls, id=kwargs.get(str("id"), no_id_given))

    def __init__(self, description, id=no_id_given, name=None):
        super(Choice, self).__init__(description, id=id, name=name)
        self.group = None

    def __unicode__(self):
        return self.desc

    def __str__(self):
        result = self.__unicode__()
        if six.PY2:
            result = result.encode("utf8")
        return result

    def __repr__(self):
        rawval = self.raw
        name = "{!r}".format(self.name)
        if name[0] in "bru":
            name = name[2:-1]
        else:
            name = name[1:-1]
        rawval = "{!r}".format(rawval)
        if rawval[0] in "bru":
            rawval = rawval[2:-1]
        else:
            rawval = rawval[1:-1]
        result = "<{}: {} (id: {}, name: {})>".format(
            self.__class__.__name__, rawval, self.id, name
        )
        if six.PY2:
            result = result.encode("utf8")
        return result


def _getter(name, given, returns, found, getter):
    def impl(
        cls,
        id,
        found=lambda id, k, v: False,
        getter=lambda id, k, v: None,
        fallback=unset,
    ):
        """Unless `fallback` is set, raises ValueError if name not present."""
        for k, v in cls.__dict__.items():
            if isinstance(v, ChoicesEntry) and found(id, k, v):
                return getter(id, k, v)
        if fallback is unset:
            raise ValueError("Nothing found for '{}'.".format(id))
        else:
            return fallback

    function = partial(impl, found=found, getter=getter)
    function.__name__ = name
    function.__doc__ = (
        "Choices.{name}({given}, fallback=unset) -> {returns}"
        "\n\nGiven the `{given}`, returns the `{returns}`. {impl_doc}"
        "".format(name=name, given=given, returns=returns, impl_doc=impl.__doc__)
    )
    return classmethod(function)


class _ChoicesMeta(type):
    def __new__(meta, classname, bases, classDict):
        groups = []
        values = []
        raw_values = []
        for k, v in classDict.items():
            if not isinstance(v, ChoicesEntry):
                continue
            v.name = k
            raw_values.append(v)
        raw_values.sort(key=lambda elem: elem.global_id)
        last_choice_id = 0
        group = None
        for choice in raw_values:
            if isinstance(choice, ChoiceGroup):
                last_choice_id = choice.id
                group = choice
                groups.append(group)
            else:
                if choice.id == no_id_given:
                    last_choice_id += 1
                    c = Choice(choice.raw, id=last_choice_id, name=choice.name)
                    d = dict(((k, getattr(choice, k)) for k in choice.__extra__))
                    choice = c.extra(**d)
                last_choice_id = choice.id
                if group is not None:
                    group.choices.append(choice)
                    choice.group = group
                    d = dict(
                        (
                            (k, getattr(group, k))
                            for k in group.__extra__
                            if k not in choice.__extra__
                        )
                    )
                    choice.extra(**d)
                values.append(choice)
                classDict[choice._ChoicesEntry__raw_name] = choice
        classDict["__groups__"] = groups
        classDict["__choices__"] = values
        return type.__new__(meta, classname, bases, classDict)


class Choices(six.with_metaclass(_ChoicesMeta, list)):
    __metaclass__ = _ChoicesMeta

    def __init__(self, filter=(unset,), item=unset, grouped=False):
        """Creates a list of pairs from the specified Choices class.
        By default, each pair consists of a numeric ID and the translated
        description. If `use_ids` is False, the name of the attribute
        is used instead of the numeric ID.

        If `filter` is specified, it's a set or sequence of attribute
        names that should be included in the list. Note that the numeric
        IDs are the same regardless of the filtering. This is useful
        for predefining a large set of possible values and filtering to
        only the ones which are currently implemented."""
        if not self.__choices__:
            raise ValueError("Choices class declared with no actual choice fields.")
        if item is unset:
            item = lambda choice: (choice.id, choice.desc)  # noqa
        filter = set(filter)
        if grouped and self.__groups__:
            for group in self.__groups__:
                group_choices = []
                for choice in group.choices:
                    if choice.name in filter or (
                        unset in filter and isinstance(choice, Choice)
                    ):
                        group_choices.append(item(choice))
                if group_choices:
                    self.append((group.desc, tuple(group_choices)))
        else:
            if grouped:
                import warnings

                warnings.warn(
                    "Choices class called with grouped=True and no actual groups."
                )
            for choice in self.__choices__:
                if choice.name in filter or (
                    unset in filter and isinstance(choice, Choice)
                ):
                    self.append(item(choice))

    from_name = _getter(
        "from_name",
        given="name",
        returns="choice object",
        found=lambda id, k, v: k == id,
        getter=lambda id, k, v: v,
    )

    id_from_name = _getter(
        "id_from_name",
        given="name",
        returns="id",
        found=lambda id, k, v: k == id,
        getter=lambda id, k, v: v.id,
    )

    desc_from_name = _getter(
        "desc_from_name",
        given="name",
        returns="localized description string",
        found=lambda id, k, v: k == id,
        getter=lambda id, k, v: v.desc,
    )

    raw_from_name = _getter(
        "raw_from_name",
        given="name",
        returns="raw description string",
        found=lambda id, k, v: k == id,
        getter=lambda id, k, v: v.raw,
    )

    from_id = _getter(
        "from_id",
        given="id",
        returns="choice object",
        found=lambda id, k, v: v.id == id,
        getter=lambda id, k, v: v,
    )

    name_from_id = _getter(
        "name_from_id",
        given="id",
        returns="attribute name",
        found=lambda id, k, v: v.id == id,
        getter=lambda id, k, v: k,
    )

    desc_from_id = _getter(
        "desc_from_id",
        given="id",
        returns="localized description string",
        found=lambda id, k, v: v.id == id,
        getter=lambda id, k, v: v.desc,
    )

    raw_from_id = _getter(
        "raw_from_id",
        given="id",
        returns="raw description string",
        found=lambda id, k, v: v.id == id,
        getter=lambda id, k, v: v.raw,
    )

    @staticmethod
    def to_ids(func):
        """Converts a sequence of choices to a sequence of choice IDs."""

        def wrapper(self):
            return (elem.id for elem in func(self))

        return wrapper

    @staticmethod
    def to_names(func):
        """Converts a sequence of choices to a sequence of choice names."""

        def wrapper(self):
            return (elem.name for elem in func(self))

        return wrapper

    Choice = Choice
    Group = ChoiceGroup

    # deprecated compatibility layer for code using lck.django.choices < 0.8
    # to be removed at 1.0
    FromName = from_name
    IDFromName = id_from_name
    DescFromName = desc_from_name
    RawFromName = raw_from_name
    FromID = from_id
    NameFromID = name_from_id
    DescFromID = desc_from_id
    RawFromID = raw_from_id
    ToIDs = to_ids
    ToNames = to_names


#
# commonly used choices
#


class Country(Choices):
    """Specifies a set for all countries of the world (as of January 2011),
    including unions, parts of United Kingdom and unrecognized states."""

    _ = Choices.Choice

    COUNTRIES = Choices.Group(0)
    """Officially recognized states, as of January 2011."""

    af = _("Afghanistan")
    al = _("Albania")
    dz = _("Algeria")
    as_ = _("American Samoa")
    ad = _("Andorra")
    ao = _("Angola")
    ai = _("Anguilla")
    aq = _("Antarctica")
    ag = _("Antigua and Barbuda")
    ar = _("Argentina")
    am = _("Armenia")
    aw = _("Aruba")
    au = _("Australia")
    at = _("Austria")
    az = _("Azerbaijan")
    bs = _("Bahamas")
    bh = _("Bahrain")
    bd = _("Bangladesh")
    bb = _("Barbados")
    by = _("Belarus")
    be = _("Belgium")
    bz = _("Belize")
    bj = _("Benin")
    bm = _("Bermuda")
    bt = _("Bhutan")
    bo = _("Bolivia")
    ba = _("Bosnia and Herzegovina")
    bw = _("Botswana")
    br = _("Brazil")
    bn = _("Brunei")
    bg = _("Bulgaria")
    bf = _("Burkina Faso")
    bi = _("Burundi")
    kh = _("Cambodia")
    cm = _("Cameroon")
    ca = _("Canada")
    cv = _("Cape Verde")
    ky = _("Cayman Islands")
    cf = _("Central African Republic")
    td = _("Chad")
    cl = _("Chile")
    cn = _("China")
    co = _("Colombia")
    km = _("Comoros")
    cg = _("Congo Brazzaville")
    cd = _("Congo Kinshasa")
    ck = _("Cook Islands")
    cr = _("Costa Rica")
    ci = _("Cote Divoire")
    hr = _("Croatia")
    cu = _("Cuba")
    cy = _("Cyprus")
    cz = _("Czech Republic")
    dk = _("Denmark")
    dj = _("Djibouti")
    dm = _("Dominica")
    do = _("Dominican Republic")
    ec = _("Ecuador")
    eg = _("Egypt")
    sv = _("El Salvador")
    gq = _("Equatorial Guinea")
    er = _("Eritrea")
    ee = _("Estonia")
    et = _("Ethiopia")
    fo = _("Faroe Islands")
    fj = _("Fiji")
    fi = _("Finland")
    fr = _("France")
    pf = _("French Polynesia")
    ga = _("Gabon")
    gm = _("Gambia")
    ge = _("Georgia")
    de = _("Germany")
    gh = _("Ghana")
    gi = _("Gibraltar")
    gr = _("Greece")
    gd = _("Grenada")
    gu = _("Guam")
    gt = _("Guatemala")
    gw = _("Guinea Bissau")
    gn = _("Guinea")
    gy = _("Guyana")
    ht = _("Haiti")
    hn = _("Honduras")
    hk = _("Hong Kong")
    hu = _("Hungary")
    is_ = _("Iceland")
    in_ = _("India")
    id = _("Indonesia")
    ir = _("Iran")
    iq = _("Iraq")
    ie = _("Ireland")
    il = _("Israel")
    it = _("Italy")
    jm = _("Jamaica")
    jp = _("Japan")
    je = _("Jersey")
    jo = _("Jordan")
    kz = _("Kazakhstan")
    ke = _("Kenya")
    ki = _("Kiribati")
    kw = _("Kuwait")
    kg = _("Kyrgyzstan")
    la = _("Laos")
    lv = _("Latvia")
    lb = _("Lebanon")
    ls = _("Lesotho")
    lr = _("Liberia")
    ly = _("Libya")
    li = _("Liechtenstein")
    lt = _("Lithuania")
    lu = _("Luxembourg")
    mo = _("Macau")
    mk = _("Macedonia")
    mg = _("Madagascar")
    mw = _("Malawi")
    my = _("Malaysia")
    mv = _("Maldives")
    ml = _("Mali")
    mt = _("Malta")
    mh = _("Marshall Islands")
    mr = _("Mauritania")
    mu = _("Mauritius")
    mx = _("Mexico")
    fm = _("Micronesia")
    md = _("Moldova")
    mc = _("Monaco")
    mn = _("Mongolia")
    me = _("Montenegro")
    ms = _("Montserrat")
    ma = _("Morocco")
    mz = _("Mozambique")
    mm = _("Myanmar")
    na = _("Namibia")
    nr = _("Nauru")
    np = _("Nepal")
    an = _("Netherlands Antilles")
    nl = _("Netherlands")
    nz = _("New Zealand")
    ni = _("Nicaragua")
    ne = _("Niger")
    ng = _("Nigeria")
    kp = _("North Korea")
    no = _("Norway")
    om = _("Oman")
    pk = _("Pakistan")
    pw = _("Palau")
    pa = _("Panama")
    pg = _("Papua New Guinea")
    py = _("Paraguay")
    pe = _("Peru")
    ph = _("Philippines")
    pl = _("Poland")
    pt = _("Portugal")
    pr = _("Puerto Rico")
    qa = _("Qatar")
    ro = _("Romania")
    ru = _("Russian Federation")
    rw = _("Rwanda")
    lc = _("Saint Lucia")
    ws = _("Samoa")
    sm = _("San Marino")
    st = _("Sao Tome and Principe")
    sa = _("Saudi Arabia")
    sn = _("Senegal")
    rs = _("Serbia")
    sc = _("Seychelles")
    sl = _("Sierra Leone")
    sg = _("Singapore")
    sk = _("Slovakia")
    si = _("Slovenia")
    sb = _("Solomon Islands")
    so = _("Somalia")
    za = _("South Africa")
    kr = _("South Korea")
    es = _("Spain")
    lk = _("Sri Lanka")
    kn = _("St Kitts and Nevis")
    vc = _("St Vincent and the Grenadines")
    sd = _("Sudan")
    sr = _("Suriname")
    sz = _("Swaziland")
    se = _("Sweden")
    ch = _("Switzerland")
    sy = _("Syria")
    tj = _("Tajikistan")
    tw = _("Taiwan")
    tz = _("Tanzania")
    th = _("Thailand")
    tl = _("Timor Leste")
    tg = _("Togo")
    to = _("Tonga")
    tt = _("Trinidad and Tobago")
    tn = _("Tunisia")
    tr = _("Turkey")
    tm = _("Turkmenistan")
    tc = _("Turks and Caicos Islands")
    tv = _("Tuvalu")
    ug = _("Uganda")
    ua = _("Ukraine")
    ae = _("United Arab Emirates")
    gb = _("United Kingdom")
    us = _("United States of America")
    uy = _("Uruguay")
    uz = _("Uzbekistan")
    vu = _("Vanuatu")
    va = _("Vatican City")
    ve = _("Venezuela")
    vn = _("Viet Nam")
    vg = _("Virgin Islands British")
    vi = _("Virgin Islands US")
    eh = _("Western Sahara")
    ye = _("Yemen")
    zm = _("Zambia")
    zw = _("Zimbabwe")

    UNITED_KINGDOM = Choices.Group(300)
    """Parts of United Kingdom."""

    england = _("England")
    northern_ireland = _("Northern Ireland")
    wales = _("Wales")
    scotland = _("Scotland")

    UNRECOGNIZED_STATES = Choices.Group(600)
    """De facto countries that are not globally recognized."""
    cy_northern = _("Northern Cyprus")
    palestine = _("Palestine")
    somaliland = _("Somaliland")

    UNIONS = Choices.Group(900)
    """Commonly referred unions and associations."""

    african_union = _("African Union")
    arab_league = _("Arab League")
    association_of_southeast_asian_nations = _("Association of Southeast Asian Nations")
    caricom = _("Caricom")
    commonwealth_of_independent_states = _("Commonwealth of Independent States")
    commonwealth_of_nations = _("Commonwealth of Nations")
    european_union = _("European Union")
    islamic_conference = _("Islamic Conference")
    nato = _("NATO")
    olimpic_movement = _("Olimpic Movement")
    opec = _("OPEC")
    red_cross = _("Red Cross")
    united_nations = _("United Nations")


def _language_lookup_getter(overrides, getter):
    def impl(cls, name, getter=lambda choice: choice, fallback=unset):
        """
        If the given `name` has ``-`` characters, they are converted to
        ``_`` for lookup purposes. If no language is found, a more generic
        language lookup is tried (e.g. for ``"pl-pl"`` also ``"pl"`` will be
        attempted) before raising ValueError or returning the fallback value.
        """
        name = name.replace("-", "_")
        name_generic = name.split("_")[0]
        if name_generic == name:
            name_generic = None
        for k, v in cls.__dict__.items():
            exact_match = k == name
            generic_match = name_generic and k == name_generic
            if isinstance(v, ChoicesEntry) and exact_match or generic_match:
                return getter(v)
        if fallback is unset:
            raise ValueError("Nothing found for '{}'.".format(id))
        else:
            return fallback

    function = partial(impl, getter=getter)
    function.__name__ = overrides.__name__
    function.__doc__ = overrides.__doc__ + " " + dedent(impl.__doc__)
    return classmethod(function)


class Language(Choices):
    """Specifies a broad set of languages. Uses a superset of values found in
    Django and Firefox sources."""

    _ = Choices.Choice

    aa = _("Afar")
    ab = _("Abkhazian")
    ae = _("Avestan")
    af = _("Afrikaans")
    ak = _("Akan")
    am = _("Amharic")
    an = _("Aragonese")
    ar = _("Arabic")
    as_ = _("Assamese")
    ast = _("Asturian")
    av = _("Avaric")
    ay = _("Aymara")
    az = _("Azerbaijani")
    ba = _("Bashkir")
    be = _("Belarusian")
    bg = _("Bulgarian")
    bh = _("Bihari")
    bi = _("Bislama")
    bm = _("Bambara")
    bn = _("Bengali")
    bo = _("Tibetan")
    br = _("Breton")
    bs = _("Bosnian")
    ca = _("Catalan")
    ce = _("Chechen")
    ch = _("Chamorro")
    co = _("Corsican")
    cr = _("Cree")
    cs = _("Czech")
    cu = _("Church Slavic")
    cv = _("Chuvash")
    cy = _("Welsh")
    da = _("Danish")
    de = _("German")
    dv = _("Divehi")
    dz = _("Dzongkha")
    ee = _("Ewe")
    el = _("Greek")
    en = _("English")
    en_gb = _("British English")
    en_us = _("American English")
    eo = _("Esperanto")
    es = _("Spanish")
    es_ar = _("Argentinian Spanish")
    et = _("Estonian")
    eu = _("Basque")
    fa = _("Persian")
    ff = _("Fulah")
    fi = _("Finnish")
    fj = _("Fijian")
    fo = _("Faroese")
    fr = _("French")
    fur = _("Friulian")
    fy = _("Frisian")
    ga = _("Irish")
    gd = _("Scots Gaelic")
    gl = _("Galician")
    gn = _("Guarani")
    gu = _("Gujarati")
    gv = _("Manx")
    ha = _("Hausa")
    he = _("Hebrew")
    hi = _("Hindi")
    ho = _("Hiri Motu")
    hr = _("Croatian")
    hsb = _("Upper Sorbian")
    ht = _("Haitian")
    hu = _("Hungarian")
    hy = _("Armenian")
    hz = _("Herero")
    ia = _("Interlingua")
    id = _("Indonesian")
    ie = _("Interlingue")
    ig = _("Igbo")
    ii = _("Sichuan Yi")
    ik = _("Inupiaq")
    io = _("Ido")
    is_ = _("Icelandic")
    it = _("Italian")
    iu = _("Inuktitut")
    ja = _("Japanese")
    jv = _("Javanese")
    ka = _("Georgian")
    kg = _("Kongo")
    ki = _("Kikuyu")
    kj = _("Kuanyama")
    kk = _("Kazakh")
    kl = _("Greenlandic")
    km = _("Khmer")
    kn = _("Kannada")
    ko = _("Korean")
    kok = _("Konkani")
    kr = _("Kanuri")
    ks = _("Kashmiri")
    ku = _("Kurdish")
    kv = _("Komi")
    kw = _("Cornish")
    ky = _("Kirghiz")
    la = _("Latin")
    lb = _("Luxembourgish")
    lg = _("Ganda")
    li = _("Limburgan")
    ln = _("Lingala")
    lo = _("Lao")
    lt = _("Lithuanian")
    lu = _("Luba-Katanga")
    lv = _("Latvian")
    mg = _("Malagasy")
    mh = _("Marshallese")
    mi = _("Maori")
    mk = _("Macedonian")
    ml = _("Malayalam")
    mn = _("Mongolian")
    mr = _("Marathi")
    ms = _("Malay")
    mt = _("Maltese")
    my = _("Burmese")
    na = _("Nauru")
    nb = _("Norwegian Bokm\u00e5l")
    nd = _("Ndebele, North")
    ne = _("Nepali")
    ng = _("Ndonga")
    nl = _("Dutch")
    nn = _("Norwegian Nynorsk")
    no = _("Norwegian")
    nr = _("Ndebele, South")
    nso = _("Sotho, Northern")
    nv = _("Navajo")
    ny = _("Chichewa")
    oc = _("Occitan")
    oj = _("Ojibwa")
    om = _("Oromo")
    or_ = _("Oriya")
    os = _("Ossetian")
    pa = _("Punjabi")
    pi = _("Pali")
    pl = _("Polish")
    ps = _("Pashto")
    pt = _("Portuguese")
    pt_br = _("Brazilian Portugese")
    qu = _("Quechua")
    rm = _("Rhaeto-Romanic")
    rn = _("Kirundi")
    ro = _("Romanian")
    ru = _("Russian")
    rw = _("Kinyarwanda")
    sa = _("Sanskrit")
    sc = _("Sardinian")
    sd = _("Sindhi")
    se = _("Northern Sami")
    sg = _("Sango")
    si = _("Singhalese")
    sk = _("Slovak")
    sl = _("Slovenian")
    sm = _("Samoan")
    sn = _("Shona")
    so = _("Somali")
    sq = _("Albanian")
    sr = _("Serbian")
    sr_latn = _("Serbian Latin")
    ss = _("Siswati")
    st = _("Sotho, Southern")
    su = _("Sundanese")
    sv = _("Swedish")
    sw = _("Swahili")
    ta = _("Tamil")
    te = _("Telugu")
    tg = _("Tajik")
    th = _("Thai")
    ti = _("Tigrinya")
    tig = _("Tigre")
    tk = _("Turkmen")
    tl = _("Tagalog")
    tlh = _("Klingon")
    tn = _("Tswana")
    to = _("Tonga")
    tr = _("Turkish")
    ts = _("Tsonga")
    tt = _("Tatar")
    tw = _("Twi")
    ty = _("Tahitian")
    ug = _("Uighur")
    uk = _("Ukrainian")
    ur = _("Urdu")
    uz = _("Uzbek")
    ve = _("Venda")
    vi = _("Vietnamese")
    vo = _("Volap\u00fck")
    wa = _("Walloon")
    wen = _("Sorbian")
    wo = _("Wolof")
    xh = _("Xhosa")
    yi = _("Yiddish")
    yo = _("Yoruba")
    za = _("Zhuang")
    zh = _("Chinese")
    zh_cn = _("Simplified Chinese")
    zh_tw = _("Traditional Chinese")
    zu = _("Zulu")

    from_name = _language_lookup_getter(
        overrides=Choices.from_name, getter=lambda choice: choice
    )

    id_from_name = _language_lookup_getter(
        overrides=Choices.id_from_name, getter=lambda choice: choice.id
    )

    desc_from_name = _language_lookup_getter(
        overrides=Choices.desc_from_name, getter=lambda choice: choice.desc
    )

    raw_from_name = _language_lookup_getter(
        overrides=Choices.raw_from_name, getter=lambda choice: choice.raw
    )

    # deprecated compatibility layer for code using lck.django.choices < 0.8
    # to be removed at 1.0
    FromName = from_name
    IDFromName = id_from_name
    DescFromName = desc_from_name
    RawFromName = raw_from_name


class Gender(Choices):
    _ = Choices.Choice

    female = _("female")
    male = _("male")
    unspecified = _("unspecified")
