# pipeline/prompt_builder.py
from datetime import datetime
from typing import Dict, List, Optional


def build_prompt(
    question: str,
    context: Dict,
    question_type: Optional[str] = None,   # ← NEW
) -> List[Dict]:
    """
    Stage-4 – construct chat prompt.
    If the question type is 'semantic_context_word', add an
    instruction to perform  التحليل الدلالي للكلمة ضمن السياق القرآني.
    """
    extra = ""
    if question_type == "semantic_context_word":
        extra = (
            "\nركّز على التحليل الدلالي للكلمة ضمن السياق القرآني "
            "الذي ظهرت فيه."
        )
    elif question_type == "frequency_word_root":
        extra = (
            "\nأعلن عدد التكرارات بدقة ثم استعرض قائمة المراجع القرآنية "
            "بصيغـة «سورة رقم آية رقم» مفصولة بفواصل، مستفيدًا من القائمة "
            "occurrence_refs_pretty داخل السياق."
        )
    elif question_type == "difference_two_words":
        extra = (
            "\nأنت محلل لغوي متخصص في الفروق الدلالية بين الكلمات القرآنية. "
            "قارن بين الكلمتين المذكورتين في السؤال من حيث:\n"
            "1. المعنى الأساسي لكل كلمة\n"
            "2. الفروق الدلالية والاستخدامات المختلفة\n"
            "3. السياقات القرآنية التي ظهرت فيها كل كلمة\n"
            "4. الأوزان الصرفية والاشتقاقات إن وجدت\n"
            "قدم إجابة مفصلة ومقارنة شاملة بين الكلمتين."
        )
    elif question_type == "root_ayah_extraction":
        extra = (
            "\nأدرج *جميع* الآيات المُدرجة فى المفتاح ayah_extraction كما هى، "
            "ويُرجى كتابة *اسم السورة* بدل رقمها متبوعًا برقم الآية على صورة "
            "«سورة البقرة آية 255» مثلًا. لا تَسْقِط أى آية ولا تُعيد ترقيمها."
        )
    elif question_type == "roots_by_topic":
        extra = (
            """
التعليمات (Instructions)
	1.	أنت باحث لغوي مُتخصّص في الجذور العربية واستعمالها القرآني.
	2.	ستستلم في كل مثال كتلتين واضحتين:
	•	وسْم <question> … </question> يحوي سؤالاً بالعربية عن مجموعة جذور تدلّ على معنى معيّن.
	•	وسْم <context> … </context> يحوي:
	•	topic_expansion_note – سطر توصيفي.
	•	topic_expansion – يحتوي:
	•	‎root_list ↩️ قائمة أوّلية من 9 جذور مرشّحة (نصّيّاً فقط).
	•	‎rows ↩️ معلومات معجميّة مختصرة حول كل جذر.
	•	‎root_samples – آيات قرآنية مرتبطة بكل جذر.
	3.	مهمّتك هي تصنيف الجذور الأكثر صلة بالسؤال ثم كتابة الإجابة حصراً وفق القالب الموضَّح أدناه بدون أي إضافات أو شروح جانبيّة.
	4.	آليّة العمل الموصى بها:
a. راجع الجذور داخل ‎root_list.
b. احذف أي جذر لا يخدم معنى السؤال بوضوح.
c. إن احتجت لتبديل ترتيبها، قُم بذلك من الأكثر إلى الأقل صلة.
d. احتفِظ بأقصى حدّ 9 جذور.
	5.	لكل جذر مختار:
	•	اكتب كلمة أو كلمتين تلخّص معناه الأساسي (مأخوذة من معجم «لسان العرب» في rows).
	•	اكتب جملة تشرح علاقته بموضوع السؤال.
	•	استخرج آية واحدة من root_samples تعبّر عن تلك العلاقة، ثم انسخها كما هي (النص العربي فقط دون رقم السورة أو الآية).
	6.	يجب أن تكون الإجابة بكاملها باللغة العربية الفصحى.
	7.	استخدم القالب بالضبط؛ لا تغيّر العناوين، علامات الترقيم أو ترتيب الفقرات.
	8.	لا تذكر هذه التعليمات في المخرَج.

⸻

قالب الإخراج (Output Template – انسخه كما هو):

قائمة بالجذور المرشحة: الجذر ١، الجذر ٢، الجذر ٣، الجذر ٤، الجذر ٥، الجذر ٦، الجذر ٧، الجذر ٨، الجذر ٩
١
الجذر: ………
شرح الجذر: ………
علاقته بالموضوع: ………
مثال: ………
٢
الجذر: ………
شرح الجذر: ………
علاقته بالموضوع: ………
مثال: ………
٣
الجذر: ………
شرح الجذر: ………
علاقته بالموضوع: ………
مثال: ………
✧ ملاحظة: سيقدم 9 جذور في السياق، عليك ان تشرح مالا يقل عن 5 جذور ومالا يزيد عن 9 جذور.

       """ )

    system_msg = (
        "You are a meticulous Quranic linguistics assistant. "
        "Answer strictly from <context/>, citing nothing else. "
        "If the answer is absent, say you do not know."
        f"{extra}\nUTC-timestamp: {datetime.utcnow().isoformat(timespec='seconds')}"
    )

    ctx_str = "\n".join(f"{k}: {v}" for k, v in context.items() if v)

    user_msg = (
        f"<question>\n{question}\n</question>\n"
        f"<context>\n{ctx_str}\n</context>"
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]