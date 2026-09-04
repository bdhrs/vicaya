# Phase 1 — corpus (T3)

Built 2026-09-03. Sampled from the live index (`$VICAYA_LIBRARY_FOLDERS_INDEX`, read-only query), not filtered by size or page count.

## Population

`SELECT source_path FROM documents WHERE extraction_status='empty' AND lower(extension)='.pdf'` → **1,735** rows at the time of sampling (spec cites 1,739; the small drift is expected — a run may be in progress and finished books flip out of `empty`).

## Sampling method

`random.seed(20260903)`; `random.sample(pool, 20)` over the 1,733 non-staller PDFs, plus the two named stallers appended by exact path match (both found in the pool). Reproducible from the seed and this method — no size/page filter applied at any step.

## The 22 books

| Pages | Path | Note |
|---:|---|---|
| 108 | `SBS Textual/Tipitaka/Englisch/Tip. - PTS/2 Suttapitaka/5 Khuddaka Nikaya/The Udana; Peter Masefield.pdf` | |
| 93 | `Bodhirasa eBook Library/Ven. Medawachchiye Dhammajothi/The Concept of Emptiness in Pali Literature (5443)/The Concept of Emptiness in Pali Literatur - Ven. Medawachchiye Dhammajothi.pdf` | |
| 708 | `Bodhirasa eBook Library/Maurice Winternitz/A History of Indian Literature Vol. 2_ Buddhist Literature and Jaina Literature (15124)/A History of Indian Literature Vol. 2_ Bud - Maurice Winternitz.pdf` | |
| 34 | `Bodhirasa eBook Library/Eric M. Greene/Seeing Avijnapti-rupa_ Buddhist Doctrine and Meditative Experience in India and China (10510)/Seeing Avijnapti-rupa_ Buddhist Doctrine a - Eric M. Greene.pdf` | |
| 56 | `Na Uyana eBook Library/Buddhist Books/Journals, Articles etc/buddhist modernism and the rhetoric of meditative experience.pdf` | |
| 340 | `SBS Textual/Tipitaka/Pali/Tip. - PTS/Others/Saddaniti/Saddaniti - III (Sattamala).pdf` | |
| 119 | `Bodhirasa eBook Library/K.R. Norman (Editor)/Journal of the Pali Text Society 1994 (7403)/Journal of the Pali Text Society 1994 - K.R. Norman (Editor).pdf` | |
| 34 | `Bodhirasa eBook Library/Yagya Sharma/Chanakya (13331)/Chanakya - Yagya Sharma.pdf` | |
| 108 | `Bodhirasa eBook Library/Paul Demieville/Buddhism & Healing_ Demieville's Article _Byo_ from Hobogirin (15483)/Buddhism & Healing_ Demieville's Article _ - Paul Demieville.pdf` | |
| 150 | `Bodhirasa eBook Library/L.P.N. Perera/Sexuality in Ancient India - A Stud (3169)/Sexuality in Ancient India - A  - L.P.N. Perera.pdf` | |
| 1 | `Bodhirasa eBook Library/Unknown/Optical illusion (3564)/Optical illusion - Unknown.pdf` | 1-page edge case |
| 312 | `Bodhirasa eBook Library/Pali Text Society/Samyutta Nikaya Part 2_ Nidana Vagga (6888)/Samyutta Nikaya Part 2_ Nidana Vagga - Pali Text Society.pdf` | |
| 246 | `Bodhirasa eBook Library/David J. Kalupahana/Principles of Buddhist Psychology (6338)/Principles of Buddhist Psycholo - David J. Kalupahana.pdf` | |
| 58 | `Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & Articles in English/08. History of Buddhism/Buddhism in Thailand/ThaiWomenInBuddhism.pdf` | |
| 4 | `SBS Textual/Texts English/1 Theravada/01 Authors/1 Monks/Analayo, Ven/Lectures/Anguttara Nikaya - selected discourses/AN8.70.pdf` | |
| 4 | `Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & Articles in English/12. Monastic Teachers/Bhikkhu Analayo/Articles in the Encyclopedia of Buddhism/SamannaphalaSutta.pdf` | |
| 85 | `Bodhirasa eBook Library/Charles S. Prebish/Survey of Vinaya Literature. Vol. I (10690)/Survey of Vinaya Literature. Vol. I - Charles S. Prebish.pdf` | |
| 94 | `Na Uyana eBook Library/Others/Human Types - Raymond Firth.pdf` | |
| 11 | `Bodhirasa eBook Library/Johannes Bronkhorst/On the Genesis of Buddhism in Its Historical Context (15774)/On the Genesis of Buddhism in Its Historic - Johannes Bronkhorst.pdf` | |
| 2 | `Na Uyana eBook Library/Buddhist Books/Journals, Articles etc/Richard Gombrich/richard28.pdf` | 2-page edge case |
| 587 | `Bodhirasa eBook Library/W.H. Newton-Smith/Companion to the Philosophy Of Scie (3800)/Companion to the Philosophy Of - W.H. Newton-Smith.pdf` | **named staller** |
| 456 | `Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & Articles in English/17. Buddhism in Verious Topics/Psychoanalysis and Buddhism.PDF` | **named staller** |

All paths are relative to `$VICAYA_LIBRARY_FOLDERS` (`/home/bodhirasa/MyFiles/2_Resources/Libraries`). Full absolute paths and the generating script live in the session scratchpad (`corpus_paths.txt`, `corpus_pages.tsv`) — not committed, reproducible from the seed above.

## Summary

n=22, total pages=3,610, min=1, max=708 (median ≈97, in line with the population's stated median of 94 — sample is not skewed toward large books).
