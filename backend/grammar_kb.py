import re
from typing import Any, Dict, List, Optional, Tuple

GRAMMAR_CATALOG: List[Dict[str, Any]] = [
    # --- JLPT N5 ---
    {
        "pattern": "〜てはいけない",
        "regex": r"(?:て|で)は(?:いけない|いけません|だめ(?:だ|です)?)",
        "jlpt": "N5",
        "meaning": "must not; may not (prohibition)",
        "formation": "Verb [て-form] + はいけない",
        "explanation": "Expresses a strong prohibition or rule stating that someone must not do something.",
        "examples": ["ここでタバコを吸ってはいけない。", "部屋に入ってはいけません。"]
    },
    {
        "pattern": "〜てもいい",
        "regex": r"(?:て|で)も(?:いい|よい|かまわない|構いません)(?:です|か)?",
        "jlpt": "N5",
        "meaning": "may; can; it is okay to (permission)",
        "formation": "Verb [て-form] + もいい",
        "explanation": "Used to give or ask for permission to do an action.",
        "examples": ["写真を撮ってもいいですか。", "もう帰ってもいいですよ。"]
    },
    {
        "pattern": "〜なければならない",
        "regex": r"(?:なければ|なきゃ|ないと)(?:ならない|なりません|いけない|いけません|だめ)",
        "jlpt": "N5",
        "meaning": "must; have to do (obligation)",
        "formation": "Verb [ない-stem] + ければならない",
        "explanation": "Indicates an obligation or necessity where the speaker or subject has no choice.",
        "examples": ["明日早く起きなければならない。", "薬を飲まないといけない。"]
    },
    {
        "pattern": "〜たことがある",
        "regex": r"(?:た|だ)ことが(?:ある|あります|ない|ありません)",
        "jlpt": "N5",
        "meaning": "have had the experience of doing",
        "formation": "Verb [た-form] + ことがある",
        "explanation": "Refers to past experience at least once in one's life.",
        "examples": ["富士山に登ったことがある。", "日本へ行ったことがありますか。"]
    },
    {
        "pattern": "〜ている",
        "regex": r"(?:て|で)(?:いる|います|いた|いました|る|ない)",
        "jlpt": "N5",
        "meaning": "is doing (progressive) / state of being",
        "formation": "Verb [て-form] + いる",
        "explanation": "Describes an ongoing action or the continuous state resulting from a past change.",
        "examples": ["今、本を読んでいる。", "田中さんは結婚している。"]
    },
    {
        "pattern": "〜たり〜たりする",
        "regex": r"(?:たり|だり).+?(?:たり|だり)(?:する|します|した|しています)",
        "jlpt": "N5",
        "meaning": "do things like A and B (non-exhaustive listing)",
        "formation": "Verb [た-form] + り + Verb [た-form] + りする",
        "explanation": "Lists representative actions among others of a similar nature.",
        "examples": ["休日は映画を見たり本を読んだりする。"]
    },
    {
        "pattern": "〜前(に)",
        "regex": r"(?:る|う|つ|く|ぐ|す|む|ぬ|ぶ)前(?:に)?",
        "jlpt": "N5",
        "meaning": "before doing",
        "formation": "Verb [Dictionary form] / Noun + の + 前に",
        "explanation": "Designates an action taking place prior to another event.",
        "examples": ["寝る前に歯を磨きます。", "食事の前に手を洗う。"]
    },
    {
        "pattern": "〜後(で)",
        "regex": r"(?:た|だ)後(?:で|に)?",
        "jlpt": "N5",
        "meaning": "after doing",
        "formation": "Verb [た-form] / Noun + の + 後で",
        "explanation": "Designates an action taking place subsequently to another event.",
        "examples": ["ご飯を食べた後で、散歩しよう。"]
    },

    # --- JLPT N4 ---
    {
        "pattern": "〜ようにする",
        "regex": r"ように(?:する|します|している|してください)",
        "jlpt": "N4",
        "meaning": "try to; make an effort to",
        "formation": "Verb [Dictionary / ない-form] + ようにする",
        "explanation": "Expresses conscious, repeated effort to form a habit or ensure a condition is met.",
        "examples": ["毎朝野菜を食べるようにしている。", "遅刻しないようにしてください。"]
    },
    {
        "pattern": "〜ようになる",
        "regex": r"ように(?:なる|なります|なった|なりました)",
        "jlpt": "N4",
        "meaning": "reach the point where; come to be able to",
        "formation": "Verb [Dictionary / Potential form] + ようになる",
        "explanation": "Indicates a gradual change of state or acquiring an ability over time.",
        "examples": ["日本語が話せるようになった。", "刺身が食べられるようになりました。"]
    },
    {
        "pattern": "〜てみる",
        "regex": r"(?:て|で)(?:みる|みます|みた|みよう|みてください)",
        "jlpt": "N4",
        "meaning": "try doing (to see what happens)",
        "formation": "Verb [て-form] + みる",
        "explanation": "Indicates attempting an action experimentally or for the first time to experience it.",
        "examples": ["納豆を食べてみた。", "新しい靴を履いてみます。"]
    },
    {
        "pattern": "〜てしまう",
        "regex": r"(?:てしまう|てしまいます|てしまった|ちゃう|ちゃった|でしまう|じゃう|じゃった)",
        "jlpt": "N4",
        "meaning": "finish completely / regretful action",
        "formation": "Verb [て-form] + しまう / ちゃう",
        "explanation": "Expresses completion of an action, or regret/unintentional occurrence.",
        "examples": ["宿題を全部やってしまった。", "財布を忘れてしまった。"]
    },
    {
        "pattern": "〜ば〜ほど",
        "regex": r"(?:ば|なら|たら).+?ほど",
        "jlpt": "N4",
        "meaning": "the more... the more...",
        "formation": "Verb [ば-form] + Verb [Plain] + ほど",
        "explanation": "Indicates that as one condition advances, the degree of another outcome increases in proportion.",
        "examples": ["練習すればするほど上手になる。", "考えれば考えるほど分からない。"]
    },
    {
        "pattern": "〜そうだ (様態・伝聞)",
        "regex": r"(?:そう(?:だ|です|な|に)?)(?=[^あ-ん]|$)",
        "jlpt": "N4",
        "meaning": "looks like; appears to be (conjecture) / I heard that (hearsay)",
        "formation": "Verb Stem + そうだ (looks like) / Plain sentence + そうだ (hearsay)",
        "explanation": "Used for visual impression/conjecture or reporting hearsay information.",
        "examples": ["雨が降りそうだ。", "明日は雪が降るそうだ。"]
    },
    {
        "pattern": "〜やすい / 〜にくい",
        "regex": r"(?:やすい|やすく|やすかった|にくい|にくく|にくかった)",
        "jlpt": "N4",
        "meaning": "easy to do / hard to do",
        "formation": "Verb [Stem] + やすい / にくい",
        "explanation": "Expresses ease or difficulty of performing an action or inherent propensity.",
        "examples": ["このペンは書きやすい。", "彼の説明は分かりにくい。"]
    },
    {
        "pattern": "〜すぎる",
        "regex": r"(?:すぎ(?:る|ます|た|て|ない))",
        "jlpt": "N4",
        "meaning": "too much; excessively",
        "formation": "Verb [Stem] / い-Adj [drop い] / な-Adj + すぎる",
        "explanation": "Indicates that an action or property exceeds normal, acceptable bounds.",
        "examples": ["食べすぎてお腹が痛い。", "この問題は難しすぎる。"]
    },

    # --- JLPT N3 ---
    {
        "pattern": "〜わけにはいかない",
        "regex": r"わけ(?:に|で)は(?:いかない|いきません|いかないのだ)",
        "jlpt": "N3",
        "meaning": "cannot afford to; impossible due to social/moral reasons",
        "formation": "Verb [Dictionary form] + わけにはいかない",
        "explanation": "Used when psychological, moral, situational, or social pressure prevents doing an action.",
        "examples": ["大事な試験があるから、休むわけにはいかない。", "秘密を話すわけにはいきません。"]
    },
    {
        "pattern": "〜わけがない",
        "regex": r"わけが(?:ない|ありません)",
        "jlpt": "N3",
        "meaning": "there is no way that; it is impossible that",
        "formation": "Verb/Adj [Plain form] + わけがない",
        "explanation": "Strong conviction that something is completely impossible or baseless.",
        "examples": ["あんなに真面目な彼が嘘をつくわけがない。"]
    },
    {
        "pattern": "〜に違いない",
        "regex": r"に(?:違いない|ちがいない|違いありません)",
        "jlpt": "N3",
        "meaning": "must be; bound to be; without doubt",
        "formation": "Noun / Plain form + に違いない",
        "explanation": "Expresses strong confidence or subjective certainty that something is true.",
        "examples": ["犯人は彼に違いない。", "夜遅くまで働いたから疲れているに違いない。"]
    },
    {
        "pattern": "〜にもかかわらず",
        "regex": r"にも(?:かかわらず|拘らず)",
        "jlpt": "N3",
        "meaning": "despite; in spite of; although",
        "formation": "Verb/Adj/Noun [Plain form] + にもかかわらず",
        "explanation": "Indicates an unexpected result that contradicts normal assumptions from the first clause.",
        "examples": ["雨が降っているにもかかわらず、試合は行われた。", "体調が悪いにもかかわらず出社した。"]
    },
    {
        "pattern": "〜おかげで / 〜せいで",
        "regex": r"(?:おかげ(?:で|だ)|せい(?:で|だ|か))",
        "jlpt": "N3",
        "meaning": "thanks to (positive) / because of (negative fault)",
        "formation": "Noun + の / Verb [Plain] + おかげで・せいで",
        "explanation": "Attributes a result to a specific cause: おかげで for gratitude, せいで for blame.",
        "examples": ["先生のおかげで合格できた。", "台風のせいで電車が止まった。"]
    },
    {
        "pattern": "〜たびに",
        "regex": r"(?:たび|度)に",
        "jlpt": "N3",
        "meaning": "each time; whenever",
        "formation": "Verb [Dictionary form] / Noun + の + たびに",
        "explanation": "Every single time this condition occurs, the following outcome inevitably follows.",
        "examples": ["この曲を聴くたびに、子供の頃を思い出す。"]
    },
    {
        "pattern": "〜に関して / 〜について",
        "regex": r"に(?:関して|かんして|ついて)(?:は|も|の)?",
        "jlpt": "N3",
        "meaning": "regarding; concerning; about",
        "formation": "Noun + に関して / について",
        "explanation": "Introduces the topic or theme under discussion; に関して is more formal than について.",
        "examples": ["この事件に関して詳しい調査が行われている。", "日本の文化について発表します。"]
    },
    {
        "pattern": "〜にとって",
        "regex": r"にとって(?:は|も|の)?",
        "jlpt": "N3",
        "meaning": "for; to; from the perspective of",
        "formation": "Noun + にとって",
        "explanation": "Specifies whose point of view, evaluation, or stake is being considered.",
        "examples": ["若者にとってスマートフォンのない生活は考えられない。"]
    },
    {
        "pattern": "〜に対して",
        "regex": r"に(?:対して|たいして)(?:は|も|の)?",
        "jlpt": "N3",
        "meaning": "towards; in contrast to; against",
        "formation": "Noun + に対して",
        "explanation": "Used for an attitude or action aimed at a target, or a direct contrast between two things.",
        "examples": ["お客様に対して丁寧な言葉遣いをする。", "兄が活発なのに対して弟は物静かだ。"]
    },
    {
        "pattern": "〜たとたん(に)",
        "regex": r"(?:た|だ)(?:とたん|途端)(?:に)?",
        "jlpt": "N3",
        "meaning": "just as; the moment that",
        "formation": "Verb [た-form] + とたんに",
        "explanation": "Describes an instantaneous, often surprising reaction immediately following an action.",
        "examples": ["立ち上がったとたんに、めまいがした。"]
    },
    {
        "pattern": "〜かける / 〜かけの",
        "regex": r"(?:かけ(?:る|た|て|の|だ))",
        "jlpt": "N3",
        "meaning": "in the middle of doing; about to; uncompleted",
        "formation": "Verb [Stem] + かける",
        "explanation": "Expresses an action started but interrupted before completion, or on the verge of occurring.",
        "examples": ["読みかけの本が机の上に置いてある。", "溺れかけた子供を助けた。"]
    },

    # --- JLPT N2 ---
    {
        "pattern": "〜ざるを得ない",
        "regex": r"ざるを(?:得ない|えない|得ません)",
        "jlpt": "N2",
        "meaning": "cannot help but; have no choice but to",
        "formation": "Verb [ない-stem] + ざるを得ない (する becomes せざるを得ない)",
        "explanation": "Indicates that one is reluctantly forced by circumstances to take an action.",
        "examples": ["これだけの証拠があれば、事実を認めざるを得ない。"]
    },
    {
        "pattern": "〜にすぎない",
        "regex": r"に(?:すぎない|過ぎない|すぎません)",
        "jlpt": "N2",
        "meaning": "nothing more than; merely; just",
        "formation": "Noun / Verb [Plain] + にすぎない",
        "explanation": "Emphasizes that something is not extraordinary, significant, or beyond what is stated.",
        "examples": ["それは単なる偶然にすぎない。", "私は自分の義務を果たしたにすぎません。"]
    },
    {
        "pattern": "〜をめぐって",
        "regex": r"を(?:巡って|めぐって)(?:は|も|の)?",
        "jlpt": "N2",
        "meaning": "concerning; over; dispute surrounding",
        "formation": "Noun + をめぐって",
        "explanation": "Used when multiple parties argue, dispute, or have opinions centering on an issue.",
        "examples": ["遺産の相続をめぐって激しい争いが起きた。"]
    },
    {
        "pattern": "〜に伴って",
        "regex": r"に(?:伴って|ともなって|伴い)(?:は|も)?",
        "jlpt": "N2",
        "meaning": "as; along with; in conjunction with",
        "formation": "Noun / Verb [Dictionary form] + に伴って",
        "explanation": "A major change in one condition brings about a corresponding change in another.",
        "examples": ["人口の増加に伴って、様々な問題が生じている。"]
    },
    {
        "pattern": "〜に沿って",
        "regex": r"に(?:沿って|そって|沿い)(?:は|も|の)?",
        "jlpt": "N2",
        "meaning": "along; in accordance with (guideline/plan)",
        "formation": "Noun + に沿って",
        "explanation": "Following a physical path or adhering closely to rules, principles, or a predetermined plan.",
        "examples": ["マニュアルに沿って作業を進めてください。", "川に沿って桜並木が続いている。"]
    },
    {
        "pattern": "〜どころか",
        "regex": r"どころか",
        "jlpt": "N2",
        "meaning": "far from; on the contrary; let alone",
        "formation": "Noun / Verb [Plain] + どころか",
        "explanation": "Contrasts reality with an expectation, showing reality is much worse or radically different.",
        "examples": ["感謝されるどころか、文句を言われた。"]
    },

    # --- JLPT N1 ---
    {
        "pattern": "〜極まりない",
        "regex": r"(?:極まりない|きわまりない|極まる)",
        "jlpt": "N1",
        "meaning": "extremely; endlessly; knows no bounds",
        "formation": "な-Adj stem / い-Adj stem + 極まりない",
        "explanation": "Formal expression meaning an emotion, condition, or attitude is at its absolute peak.",
        "examples": ["彼の無礼極まりない態度に怒りを禁じ得ない。"]
    },
    {
        "pattern": "〜を皮切りに",
        "regex": r"を(?:皮切りに|かわきりに)(?:して)?",
        "jlpt": "N1",
        "meaning": "starting with; beginning with (spurring a series)",
        "formation": "Noun + を皮切りに",
        "explanation": "Marks the first in an expanding, consecutive series of similar actions or events.",
        "examples": ["東京公演を皮切りに、全国ツアーが始まる。"]
    },
    {
        "pattern": "〜たるもの",
        "regex": r"たるもの(?:は)?",
        "jlpt": "N1",
        "meaning": "as a (professional/leader); in the capacity of",
        "formation": "Noun + たるもの",
        "explanation": "Emphasizes the standard of conduct or duty expected of someone in a noble or responsible role.",
        "examples": ["指導者たるものは、常に公平でなければならない。"]
    },
    {
        "pattern": "〜と相まって",
        "regex": r"と(?:相まって|あいまって)",
        "jlpt": "N1",
        "meaning": "coupled with; combined with",
        "formation": "Noun + と相まって",
        "explanation": "Multiple factors working together to produce a compounded or synergistic result.",
        "examples": ["好天候と相まって、観光客が押し寄せた。"]
    },
]


def find_candidate_grammar(sentence: str) -> List[Dict[str, Any]]:
    """
    Scans a Japanese sentence against the grammar catalog.
    Returns matched grammar points with character offsets, JLPT level,
    meaning, formation, and explanation.
    """
    results: List[Dict[str, Any]] = []
    seen_ranges: List[Tuple[int, int]] = []

    for entry in GRAMMAR_CATALOG:
        pattern_regex = re.compile(entry["regex"])
        for match in pattern_regex.finditer(sentence):
            start, end = match.span()

            # Check for exact duplicates or heavy overlap
            overlap = False
            for prev_start, prev_end in seen_ranges:
                if max(start, prev_start) < min(end, prev_end):
                    overlap = True
                    break

            if not overlap:
                seen_ranges.append((start, end))
                results.append({
                    "pattern": entry["pattern"],
                    "matched_text": sentence[start:end],
                    "start": start,
                    "end": end,
                    "jlpt": entry["jlpt"],
                    "meaning": entry["meaning"],
                    "formation": entry["formation"],
                    "explanation": entry["explanation"],
                    "examples": entry["examples"],
                })

    # Sort by start offset
    results.sort(key=lambda x: x["start"])
    return results


def annotate_sentence(sentence: str, grammar_matches: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Embeds interactive HTML tags around identified grammar points in the sentence.
    Returns the annotated HTML string and the list of detected grammar points.
    """
    if grammar_matches is None:
        grammar_matches = find_candidate_grammar(sentence)

    if not grammar_matches:
        return sentence, []

    # Sort by start position descending to replace without messing up offsets
    sorted_matches = sorted(grammar_matches, key=lambda x: x["start"], reverse=True)
    annotated = sentence

    for match in sorted_matches:
        start = match["start"]
        end = match["end"]
        matched_text = sentence[start:end]
        jlpt = match.get("jlpt", "N3")
        pattern = match.get("pattern", "")
        meaning = match.get("meaning", "").replace('"', '&quot;')
        formation = match.get("formation", "").replace('"', '&quot;')
        explanation = match.get("explanation", "").replace('"', '&quot;')

        span = (
            f'<span class="grammar-point jlpt-{jlpt.lower()}" '
            f'data-pattern="{pattern}" '
            f'data-jlpt="{jlpt}" '
            f'data-meaning="{meaning}" '
            f'data-formation="{formation}" '
            f'data-explanation="{explanation}">'
            f'{matched_text}'
            f'</span>'
        )
        annotated = annotated[:start] + span + annotated[end:]

    return annotated, grammar_matches
