# C# / .NET проект для mutator

Краткий чеклист: что должно быть в репозитории, чтобы mutator находил **сайты мутаций**, гонял **тесты** и писал `.metrics/mutate/<namespace>.edn`.

Mutator использует **crapper** (рядом `../crapper` или установленный пакет) для имён методов, Cobertura и команды `dotnet test` — правила совпадают с [crapper/docs/csharp-project.ru.md](../../crapper/docs/csharp-project.ru.md).

## Структура solution

| Что | Зачем |
|-----|--------|
| Production `.csproj` с `.cs` | Источники для мутаций (те же методы, что в `crap.edn`) |
| Test `.csproj` с `<ProjectReference>` на библиотеки | Baseline и проверка каждого мутанта через `dotnet test` |
| Имя `*Tests.csproj` / `*.Tests.csproj` или `<IsTestProject>true</IsTestProject>` | Выбор test-проекта (логика crapper) |
| **Зелёный** `dotnet test` | Без успешного baseline mutator не мутирует (exit **2**) |

Тестовый фреймворк: xUnit, NUnit или MSTest — без разницы, если `dotnet test` проходит.

## Покрытие (Coverlet)

По умолчанию mutator **не** мутирует строки, которых нет в Cobertura. Перед мутантами crapper генерирует покрытие той же командой, что для CRAP:

```text
dotnet test <Tests.csproj> --collect:XPlat Code Coverage --results-directory=.../target/coverage/csharp/...
```

В **test** `.csproj`:

```xml
<PackageReference Include="coverlet.collector" Version="6.0.4">
  <PrivateAssets>all</PrivateAssets>
  <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
</PackageReference>
```

Без `coverlet.collector` отчёт не появится → почти все сайты **непокрыты** и не запускаются. Для отладки пайплайна: `--no-coverage` (медленно, не для оценки тестов).

| Флаг | Эффект |
|------|--------|
| `--use-existing-coverage` | Не вызывать `dotnet test` для coverage; читать Cobertura с диска |
| `--no-coverage` | Считать все сайты покрытыми |
| `--coverage-command "..."` | Своя команда генерации отчёта |

## Что мутируется

| Мутируется | Не мутируется (как в crapper) |
|------------|-------------------------------|
| Методы с `{ ... }` или `=>` | Конструкторы, property accessors |
| Операторы: `&&`/`||`, сравнения, `+`/`-`, `*`/`/`, `!`, `0`/`1`, `true`/`false` | Local functions, лямбды как отдельные формы |
| C#: ещё `??` → `||` | `*Tests.cs`, каталоги `test`/`tests`/…, generated `.cs` |

`:namespace` в `.metrics/mutate/*.edn` = **`Namespace.Type`** — стыкуется с `crap.edn` и uml-viewer.

## Чем C# отличается от Java (в mutator)

| Тема | Java | C# |
|------|------|-----|
| Маркер проекта | ближайший **`pom.xml`** | **`*.csproj`**: test-проект с `ProjectReference` на библиотеку (см. crapper) |
| Baseline / мутант | `mvn -q test -DexcludeTags=no-mutate` в каталоге модуля | `dotnet test path\to\Tests.csproj` — **рабочий каталог = папка test-проекта**, не обязательно корень `.cs` |
| Покрытие | **JaCoCo** (`target/site/jacoco/jacoco.xml`) | **Coverlet Cobertura** (`coverage.cobertura.xml`, часто под `TestResults/`) |
| Строки «покрыто» | индекс JaCoCo по пути файла | индекс Cobertura по `filename` в XML (метод CRAP в crapper сопоставляет класс `Ns+Nested`) |
| Тестовый тег | `-DexcludeTags=no-mutate` встроен в умолчание | **аналога нет** — отфильтровать suite через `--test-command` |
| Границы формы | метод с **`block`** | метод с **`block`** или **`arrow_expression_clause`** (`=>`) |
| Доп. мутации | — | **`??` → `||`** (как TypeScript, но **без** `?.` / `===` / `!==`) |
| Унарный `!` | родитель `unary_expression` | родитель **`prefix_unary_expression`** (в tree-sitter) |
| Приватность в EDN | `private` в заголовке → `defn-/` | то же по ключевому слову **`private`** (`internal` / `protected` — **не** `defn-/`) |
| Discover | `*Test.java`, каталоги `test`/`tests` | `*Tests.cs` / `*Test.cs`, generated `*.Designer.cs`, … |
| Fallback без test-проекта | редко: `mvn test` по модулю | `dotnet test` по первому `.csproj` вверх от файла (обычно **бесполезно**) |

Мутации арифметики/сравнений/`&&`/`||`/`*`↔`/`/`/`!`/литералы — **общий набор Java** (не правила Go, где `/` → `*` не делается).

## Запуск

Рядом с mutator должен быть **crapper** (`../crapper`). Из каталога mutator (Windows):

```powershell
cd path\to\mutator
.\.venv\Scripts\python.exe -m mutator --root "D:\path\to\YourSolution" path\to\SomeService.cs
```

| Флаг | Эффект |
|------|--------|
| `--scan path\to\file.cs` | Список сайтов, без тестов |
| `--test-command "dotnet test path\to\App.Tests.csproj"` | Свои тесты (узкий suite) |
| `--max-workers 2` | Параллельные мутанты одного файла |
| `--changed` | Только изменённые по git файлы |
| `--mutate-all` | Перезапуск и убитых мутантов |

Коды выхода: **0** — все выполненные мутанты убиты; **2** — baseline упал; **3** — есть выживший.

Нужны **`dotnet`** в PATH, Python для mutator/crapper, успешная сборка test-проекта.

## Частые проблемы

1. **Падающие тесты** (локаль, флейки) — baseline exit 2; почините suite или сузьте `--test-command`.
2. **`dotnet test` exit ≠ 0**, но Cobertura есть — coverage может подтянуться; в stderr возможно предупреждение (как у crapper).
3. **Хелперы `.cs` в test-проекте** без суффикса `Tests` — могут попасть в обход (тот же discover, что у crapper).
4. **Полное дерево solution** — долго; начните с одного `.cs` и `--scan`.

## Минимальный smoke-test

```powershell
dotnet test path\to\MyApp.Tests.csproj
dotnet list path\to\MyApp.Tests.csproj package | findstr coverlet

.\.venv\Scripts\python.exe -m mutator --root path\to\solution --scan path\to\OneType.cs
# в выводе — сайты с form_id defn/MethodName

.\.venv\Scripts\python.exe -m mutator --root path\to\solution --max-workers 1 path\to\OneType.cs
# .metrics/mutate/*.edn с :killed / :survived
```

---

[English version](csharp-project.md)
