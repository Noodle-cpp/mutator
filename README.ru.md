# mutator

[English documentation](README.md)

Мутационное тестирование для Clojure, Java, C#, Go, TypeScript, Rust и Python. Один запуск определяет язык каждого исходного файла, применяет правила мутаций этого языка и записывает снимок, который уже читает [uml-viewer](https://github.com/unclebob/uml-viewer).

Clojure следует [clj-mutate](https://github.com/unclebob/clj-mutate). Go — [mutate4go](https://github.com/unclebob/mutate4go). Java — [mutate4java](https://github.com/unclebob/mutate4java). TypeScript, Rust и Python используют те же решения, что Java, в синтаксисе языка. Имена функций и пространств имён берутся из [crapper](https://github.com/unclebob/crapper) — по ним uml-viewer стыкуется с `.metrics/crap.edn`.

Мутант **убит**, если тесты падают или по таймауту. **Выжил**, если тесты всё ещё проходят. Сайт на строке, которую отчёт о покрытии не затрагивает, **непокрыт** и не запускается. Оценка, которую рисует uml-viewer: killed / (killed + survived).

## Запуск

```bash
./mutator
```

При первом запуске создаётся `.venv` и устанавливается инструмент. crapper должен лежать рядом с этим каталогом (`../crapper`) — оттуда берутся имена namespace и функций. Из корня проекта обходится дерево, пропускаются `test`, `spec`, `vendor`, `node_modules` и `target`, пишется `.metrics/mutate/<namespace>.edn`.

Первый прогон по дереву выполняет каждый покрытый мутант. Начните с файла, над которым работаете.

```bash
./mutator src/demo/core.clj          # один файл или каталог
./mutator --scan src/demo           # список сайтов, без тестов
./mutator --changed                 # добавления и правки по git
./mutator --mutate-all              # перезапуск и убитых мутантов
./mutator --no-coverage             # не пропускать непокрытые строки
./mutator --use-existing-coverage   # читать отчёты с диска
./mutator --test-command "pytest -q tests/test_demo.py"
./mutator --max-workers 3 src/demo/core.clj
```

После появления снимка следующий запуск **дифференциальный**: перезапускаются выжившие и все сайты в функциях с изменённым текстом. Убитые мутанты в неизменённой функции остаются убитыми. `--since-last-run` — тот же отбор. `--mutate-all` его игнорирует.

Код выхода `0`, если все выполненные мутанты убиты. `2` — baseline-тесты упали. `3` — мутант выжил. При упавшем baseline снимок не перезаписывается.

## Воркеры

Мутанты одного файла выполняются параллельно. По умолчанию один воркер на ядро. `--max-workers` задаёт потолок. Берётся меньшее из потолка, числа ядер и числа выбранных сайтов. Файлы обрабатываются по одному.

Каждый воркер — каталог под `target/mutation-workers`. Мутируемый файл — приватная копия. Модули с относительным импортом на этот файл тоже копируются, чтобы Node резолвил импорт в приватную копию. Остальное дерева — ссылки. Исходники не трогаются. Overlay снимается после завершения мутантов файла.

Baseline один раз прогоняется в реальном дереве до старта воркеров. Команда мутанта — внутри воркера, в том же каталоге, что и в реальном дереве, чтобы относительный путь `src` или `./pkg` указывал на overlay. Копия под `target/mutator-backup/` от прерванного старого запуска восстанавливается перед не-scan прогоном.

## Снимок

uml-viewer загружает каждый `*.edn` под `.metrics/mutate`. Один файл — один namespace. Java с inner class или Go с функцией и методом пишут больше одного файла. Два Go-файла в одном пакете делят один снимок; повтор одного сохраняет формы другого.

```clojure
{:version 1
 :source "src/demo/board.py"
 :namespace "demo.board.Board"
 :outcomes {"[\"src/demo/board.py\",\"demo.board.Board\",\"defn/place\",10,11,\">\",\">=\"]" :survived}
 :forms [{:id "defn/place"
          :kind "defn"
          :file "src/demo/board.py"
          :line 2
          :end-line 4
          :hash "…"
          :killed 1
          :survived 1
          :uncovered 0
          :sites 2}
         {:id "defn-/_hide"
          :kind "defn-"
          :killed 0
          :survived 0
          :uncovered 1
          :sites 1}]}
```

`:namespace` — ключ класса crapper. id формы — то, что viewer разбирает:

| id формы | Операция | Приватная |
| --- | --- | --- |
| `defn/place` | `place` | нет |
| `defn-/hide` | `hide` | да |

`:sites` — все мутации в функции, включая непокрытые. При нуле viewer печатает `---no mutation sites---`.

| Язык | `:namespace` | `:name` |
| --- | --- | --- |
| Clojure | `ns` | имя `defn` / `defn-` |
| Java | `package.Class` или `package.Outer.Inner` | имя метода |
| C# | `namespace.Type` или `namespace.Outer.Inner` | имя метода |
| Go | путь импорта пакета или `import/path.Receiver` | имя функции или метода |
| TypeScript | точечный путь модуля или `module.Class` | имя функции или метода |
| Rust | `crate::module` или `crate::module::Type` | имя функции или метода |
| Python | точечный путь модуля или `module.Class` | имя функции или метода |

`defn-` — приватная форма Clojure. В других языках: private-метод, неэкспортируемая функция Go, Python с `_`, Rust без `pub`, TypeScript `private` / `#` — `defn-/`.

## Что мутирует каждый язык

Токены внутри строк, комментариев и quoted-форм Clojure не трогаются. Замена, не компилирующаяся, валит тесты и считается убитой.

| Язык | Мутации |
| --- | --- |
| Clojure | head-символы clj-mutate: `+`/`-`, `*`/`/`, `inc`/`dec`, сравнения, `=`/`not=`, `if`/`if-not`, `when`/`when-not`, `and`/`or`, пары seq, predicate, coercion. `true`/`false` и `0`/`1` где угодно. |
| Java | `true`/`false`, `==`/`!=`, `<`/`<=`, `>`/`>=`, `+`/`-`, `*`/`/`, `&&`/`||`, удаление `!` и унарного `-`, `0`/`1`. Конструкторы не записи, как в crapper. |
| C# | набор Java плюс `??`/`||`. Конструкторы и accessors не мутируются как отдельные формы — как в crapper. |
| Go | mutate4go: `+`/`-`, `*` только в `/`, сравнения, `==`/`!=`, `true`/`false`, `&&`/`||`, `0`/`1`. |
| TypeScript | набор Java плюс `===`/`!==`, `??` в `||`, `?.` в `.`. Вызов или индекс теряет `?.` (`a?.()` → `a()`). `.js`, `.jsx`, `.mjs`, `.cjs` — те же правила. |
| Rust | набор Java (`&&`/`||`, `!`, унарный `-`). |
| Python | набор Java: `and`/`or`, `not`, `True`/`False`. |

## Тесты и покрытие

Baseline должен пройти до любого мутанта. Таймаут мутанта — в десять раз дольше baseline, минимум две секунды. `--timeout-factor` меняет множитель. `--test-command` заменяет умолчание.

| Язык | Команда | Где |
| --- | --- | --- |
| Clojure | `clj -M:spec --tag ~no-mutate` при Speclj на classpath, иначе `clj -M:test` или `bb spec` | ближайший `deps.edn` или `bb.edn` |
| Java | `mvn -q test -DexcludeTags=no-mutate` | ближайший `pom.xml` |
| C# | `dotnet test` на test-проекте, ссылающемся на библиотеку (как в crapper) | ближайший `*.Tests.csproj` |
| Go | `go test -count=1` пакета файла | ближайший `go.mod` |
| TypeScript | `npm test` | ближайший `package.json` |
| Rust | `cargo test` | ближайший `Cargo.toml` |
| Python | Python из `.venv` или `venv` с `pytest`, или `unittest discover` | ближайший файл проекта |

Покрытие генерируется командами crapper, если не `--use-existing-coverage` или `--no-coverage`. Файл вне отчёта — непокрыт, об этом сообщается.

C# / .NET: что подготовить в solution — [docs/csharp-project.ru.md](docs/csharp-project.ru.md).

## Сборка без Python (Windows)

**`mutator.exe`** включает **crapper** внутри (отдельный Python/crapper на целевой машине не нужен).

```powershell
.\scripts\build-standalone.ps1   # нужен checkout ../crapper при сборке
# → dist\mutator.exe
```

См. [Noodle-cpp/ub — STANDALONE.ru.md](https://github.com/Noodle-cpp/ub/blob/master/docs/STANDALONE.ru.md).

## Разработка

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```
