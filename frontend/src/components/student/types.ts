export type TopicLevel = "beginner" | "intermediate" | "advanced";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  topicId?: number | null;
}

export interface PreTestState {
  topicId: number;
  topicName: string;
  questions: { topic_id: number; text: string; options: string[] }[];
  answers: Record<number, number>;
  step: number;
  result: { score: number; total: number; level: TopicLevel } | null;
}

export interface QuizModalState {
  topicId: number;
  topicName: string;
  questions: { topic_id: number; text: string; options: string[] }[];
  /** LLM tarafından üretilen sorularda doğru cevap indeksleri (0-3). Varsa yerel değerlendirme yapılır. */
  correctAnswers?: number[];
  answers: Record<number, number>;
  step: number;
  done: boolean;
  /**
   * concept-check : 👍 Anladım sonrası 3 soruluk kavrama testi (LLM üretir)
   * check         : hakimiyet %100 olunca açılan seviye atlama testi
   * final         : ileri seviyeyi geçince konu final testi
   * review        : DRL öneri balonu
   */
  mode: "concept-check" | "check" | "final" | "review";
  score?: number;
  total?: number;
}

export const LEVEL_META: Record<TopicLevel, { label: string; color: string; bg: string }> = {
  beginner:     { label: "Başlangıç", color: "#60a5fa", bg: "rgba(96,165,250,.12)" },
  intermediate: { label: "Orta",      color: "#a78bfa", bg: "rgba(167,139,250,.12)" },
  advanced:     { label: "İleri",     color: "#34d399", bg: "rgba(52,211,153,.12)" },
};

export const TOPIC_ICONS = [
  "data_object", "calculate", "account_tree", "loop",
  "view_list", "dataset", "function", "folder_open",
  "error", "hub",
];

export const TOPICS = [
  "Değişkenler ve Veri Tipleri",
  "Operatörler ve İfadeler",
  "Koşul İfadeleri (if/elif/else)",
  "Döngüler (for/while)",
  "Listeler ve Tuple'lar",
  "Sözlükler ve Kümeler",
  "Fonksiyonlar",
  "Dosya İşlemleri",
  "Hata Yönetimi (try/except)",
  "Nesne Yönelimli Programlama (OOP)",
];

export const TOPIC_PROMPTS: Record<number, string[]> = {
  1: ["Değişken nedir, nasıl tanımlanır?", "int, float, str ve bool arasındaki fark nedir?", "Tip dönüşümü (type casting) nasıl yapılır?", "None nedir, ne zaman kullanılır?"],
  2: ["// ve % operatörleri ne işe yarar?", "== ile is arasındaki fark nedir?", "and, or, not nasıl çalışır?", "Karşılaştırma operatörleri nelerdir?"],
  3: ["if-elif-else nasıl yazılır?", "İç içe if kullanımını göster", "Tek satırlık (ternary) if nasıl yazılır?", "Bir sayının pozitif mi negatif mi olduğunu nasıl kontrol ederim?"],
  4: ["for döngüsü nasıl çalışır?", "while döngüsü ne zaman kullanılır?", "break ve continue ne işe yarar?", "range() fonksiyonunu açıklar mısın?"],
  5: ["Liste nasıl oluşturulur ve eleman eklenir?", "append(), remove() ve pop() farkları nelerdir?", "Liste dilimleme (slicing) nasıl yapılır?", "Tuple ile liste arasındaki fark nedir?"],
  6: ["Sözlük (dict) nasıl tanımlanır?", "Anahtar-değer çifti nasıl eklenir veya güncellenir?", "Küme (set) nedir, ne zaman kullanılır?", "Sözlükte anahtar var mı nasıl kontrol ederim?"],
  7: ["Fonksiyon nasıl tanımlanır?", "Parametre ve argüman arasındaki fark nedir?", "return ne işe yarar?", "Lambda fonksiyonu ne zaman kullanılır?"],
  8: ["Dosya nasıl açılır ve okunur?", "with open() neden kullanılır?", "CSV dosyasına nasıl yazılır?", "Dosya modları (r, w, a) ne anlama gelir?"],
  9: ["try-except nasıl kullanılır?", "Hata türlerini (ValueError, TypeError vb.) nasıl yakalarım?", "finally bloğu ne işe yarar?", "Kendi hata sınıfımı nasıl oluştururum?"],
  10: ["Sınıf (class) nasıl tanımlanır?", "__init__ metodu ne işe yarar?", "Kalıtım (inheritance) nasıl çalışır?", "self nedir, neden kullanılır?"],
};

/** Konu N için kilitli kalması gereken ön koşul konu ID'si (N-1 çalışılmadan N açılmaz). */
export const TOPIC_PREREQUISITES: Record<number, number> = {
  2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9,
};

export function masteryBadge(
  score: number,
  mastered = false,
): { label: string; color: string } {
  if (mastered)    return { label: "Tamamlandı", color: "#a78bfa" };
  if (score >= 0.7) return { label: "Hakimiyet",  color: "#34d399" };
  if (score > 0)   return { label: "Devam Ediyor", color: "#60a5fa" };
  return { label: "Başlanmadı", color: "rgba(255,255,255,.3)" };
}

let _msgCounter = 0;
export const newId = () => `m${++_msgCounter}`;
