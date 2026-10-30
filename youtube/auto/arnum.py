# Arabic numbers for the automatic YouTube videos (owner, 2026-10-30): the script says every number in words (MSA), and
# whisper's reading is turned back into numbers to check each one against the data (words or digits, either way).
import re

U_M = ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة', 'عشرة']   # with a feminine noun (3-10 take the masculine form's opposite)
U_F = ['', 'واحدة', 'اثنتان', 'ثلاث', 'أربع', 'خمس', 'ست', 'سبع', 'ثماني', 'تسع', 'عشر']
TENS = {20: 'عشرين', 30: 'ثلاثين', 40: 'أربعين', 50: 'خمسين', 60: 'ستين', 70: 'سبعين', 80: 'ثمانين', 90: 'تسعين'}
ORD_M = ['', 'الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس', 'السابع', 'الثامن', 'التاسع', 'العاشر']
ORD_F = ['', 'الأولى', 'الثانية', 'الثالثة', 'الرابعة', 'الخامسة', 'السادسة', 'السابعة', 'الثامنة', 'التاسعة', 'العاشرة']

# Counted nouns: one, two (genitive/accusative), two (nominative), 3-10 (plural), 11+ (singular, accusative), feminine?
GOAL = ('هدف واحد', 'هدفين', 'هدفان', 'أهداف', 'هدفًا', False)
POINT = ('نقطة واحدة', 'نقطتين', 'نقطتان', 'نقاط', 'نقطة', True)
MATCH = ('مباراة واحدة', 'مباراتين', 'مباراتان', 'مباريات', 'مباراة', True)
PLAYER = ('لاعب واحد', 'لاعبين', 'لاعبان', 'لاعبين', 'لاعبًا', False)
TIME = ('مرة واحدة', 'مرتين', 'مرتان', 'مرات', 'مرة', True)
MINUTE = ('دقيقة واحدة', 'دقيقتين', 'دقيقتان', 'دقائق', 'دقيقة', True)


def _unit(n, noun_fem):
    # 3-10 agree in reverse: a masculine noun takes the "feminine-looking" form (ثلاثة أهداف), a feminine one the other (ثلاث نقاط).
    return (U_F if noun_fem else U_M)[n]


def number(n, noun_fem=False):
    """The number alone, as it is said before a counted noun of that gender (11 and up)."""
    if n < 11:
        return _unit(n, noun_fem) if n > 2 else ('إحدى' if noun_fem else 'واحد') if n == 1 else ('اثنتين' if noun_fem else 'اثنين')
    if n == 11:
        return 'إحدى عشرة' if noun_fem else 'أحد عشر'
    if n == 12:
        return 'اثنتي عشرة' if noun_fem else 'اثني عشر'
    if n < 20:
        return f"{_unit(n - 10, noun_fem)} {'عشرة' if noun_fem else 'عشر'}"
    if n < 100:
        t, u = n - n % 10, n % 10
        if not u:
            return TENS[t]
        first = ('إحدى' if noun_fem else 'واحد') if u == 1 else ('اثنتين' if noun_fem else 'اثنين') if u == 2 else _unit(u, noun_fem)
        return f'{first} و{TENS[t]}'
    h = 'مئة' if n < 200 else 'مئتين' if n < 300 else f"{U_F[n // 100]}مئة"
    return h if n % 100 == 0 else f'{h} و{number(n % 100, noun_fem)}'


def count(n, noun, nom=False):
    """n with its noun: «ثلاثة أهداف», «إحدى وعشرين نقطة», «مباراتان» (nominative dual when nom)."""
    one, two, two_nom, few, many, fem = noun
    if n == 1:
        return one
    if n == 2:
        return two_nom if nom else two
    if 3 <= n <= 10:
        return f'{_unit(n, fem)} {few}'
    if n % 100 == 0:
        return f'{number(n, fem)} {many[:-2] if many.endswith("ًا") else many}'  # «مئة هدف»
    return f'{number(n, fem)} {many}'


def ordinal(n, fem=False):
    """«الثامنة», «الحادي عشر», «الحادية والعشرين»."""
    O = ORD_F if fem else ORD_M
    if n <= 10:
        return O[n]
    if n == 11:
        return 'الحادية عشرة' if fem else 'الحادي عشر'
    if n < 20:
        return f"{O[n - 10]} {'عشرة' if fem else 'عشر'}"
    t, u = n - n % 10, n % 10
    if not u:
        return 'ال' + TENS[t]
    first = ('الحادية' if fem else 'الحادي') if u == 1 else O[u]
    return f'{first} وال{TENS[t]}'


def clock(h, m):
    """A kick-off time said the Egyptian way: «الساعة التاسعة والنصف مساءً». Returns (text, the hour said)."""
    part = 'صباحًا' if 5 <= h < 12 else 'ظهرًا' if 12 <= h < 15 else 'عصرًا' if 15 <= h < 17 else 'مساءً' if h >= 17 else 'بعد منتصف الليل'
    hh = h % 12 or 12
    if m == 45:
        hh = hh % 12 + 1
    word = {1: 'الواحدة', 11: 'الحادية عشرة', 12: 'الثانية عشرة'}.get(hh) or ORD_F[hh]
    tail = {0: '', 15: ' والربع', 30: ' والنصف', 45: ' إلا ربعًا'}.get(m, f' و{count(m, MINUTE)}')
    return f'الساعة {word}{tail} {part}', hh


# ---- reading numbers back from whisper's text ----
def norm(t):
    t = re.sub('[ً-ْٰـ]', '', t)
    # The Egyptian accent says ث as ت and ذ as د («التامنة», «بتلاتة»), and whisper writes it that way.
    t = re.sub('[أإآٱ]', 'ا', t).replace('ة', 'ه').replace('ى', 'ي').replace('ث', 'ت').replace('ذ', 'د')
    return t.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))


def _m(pairs):
    return {norm(k): v for k, v in pairs}


UNITS = _m([(w, i) for i, w in enumerate(U_M) if i] + [(w, i) for i, w in enumerate(U_F) if i] + [(w[2:], i) for i, w in enumerate(ORD_M) if i] + [(w[2:], i) for i, w in enumerate(ORD_F) if i]
           + [('احد', 1), ('احدي', 1), ('حادي', 1), ('حاديه', 1), ('اثنين', 2), ('اثنتين', 2), ('اثني', 2), ('اثنتي', 2), ('اثنا', 2), ('اثنتا', 2), ('ثنتين', 2), ('ثمان', 8), ('ثمانيه', 8), ('صفر', 0)]
           + [(w[2:] + 'ًا', i) for i, w in enumerate(ORD_M) if 2 <= i <= 10])
TENW = _m([(w, t) for t, w in TENS.items()] + [(w[:-2] + 'ون', t) for t, w in TENS.items()])
HUNW = _m([('مئه', 100), ('مائه', 100), ('ميه', 100), ('مئتين', 200), ('مئتان', 200), ('مية', 100)])
DUAL = {norm(w) for w in ('هدفين', 'هدفان', 'نقطتين', 'نقطتان', 'مباراتين', 'مباراتان', 'مرتين', 'مرتان', 'لاعبين', 'لاعبان', 'دقيقتين', 'هزيمتين', 'تعادلين', 'انتصارين', 'فوزين')}
ONE = {norm(w) for w in ('هدف',)}
PRE = ['وبال', 'وال', 'بال', 'فال', 'كال', 'ولل', 'لل', 'ال', 'وب', 'ول', 'و', 'ب', 'ل', 'ف']


def _variants(tok):
    yield tok
    for p in PRE:
        if tok.startswith(p) and len(tok) - len(p) >= 2:
            yield tok[len(p):]


def _kind(tok):
    if tok.isdigit():
        return 'n', int(tok)
    for v in _variants(tok):
        if v in UNITS: return 'u', UNITS[v]
        if v in TENW: return 't', TENW[v]
        if v in HUNW: return 'h', HUNW[v]
        if v in DUAL: return 'n', 2
        if v in ONE: return 'n', 1
    return None, None


def numbers_in(text):
    """Every number said in a text, in order: «سبعة وسبعين» → 77, «الحادية عشرة» → 11, «هدفين» → 2, «2-1» → 2, 1."""
    toks = [t for t in re.split(r'[^\w]+', norm(text)) if t]
    out, i = [], 0
    while i < len(toks):
        k, v = _kind(toks[i])
        if k is None:
            i += 1; continue
        nk, nv = _kind(toks[i + 1]) if i + 1 < len(toks) else (None, None)
        if k == 'u' and i + 1 < len(toks) and toks[i + 1] in ('عشر', 'عشره') and v < 10:
            out.append(v + 10); i += 2; continue
        if k in ('u', 'n') and v < 10 and nk == 't':
            out.append(v + nv); i += 2; continue
        if k == 'h' and nk in ('u', 't'):
            nnk, nnv = _kind(toks[i + 2]) if i + 2 < len(toks) else (None, None)
            if nk == 'u' and nnk == 't':
                out.append(v + nv + nnv); i += 3; continue
            out.append(v + nv); i += 2; continue
        out.append(v); i += 1
    return out
