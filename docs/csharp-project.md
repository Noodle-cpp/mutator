# C# / .NET project layout for mutator

Short checklist for **mutation sites**, **test runs**, and `.metrics/mutate/<namespace>.edn`.

Mutator relies on **crapper** (`../crapper` or an installed package) for method names, Cobertura, and `dotnet test` discovery — same rules as [crapper/docs/csharp-project.md](../../crapper/docs/csharp-project.md).

## Solution layout

- **Production** `.csproj` with `.cs` sources (same methods as in `crap.edn`).
- **Test** `.csproj` with **ProjectReference** to those libraries.
- Test project named `*Tests.csproj` / `*.Tests.csproj`, or `<IsTestProject>true</IsTestProject>`.
- **`dotnet test` must pass** before mutants run (exit **2** on baseline failure).

## Coverage

By default, mutator skips sites on lines missing from Cobertura. Coverage is generated with crapper’s C# runner (XPlat Code Coverage + **coverlet.collector** on the test project).

Without Coverlet, almost everything is **uncovered** and not executed. Use `--no-coverage` only to debug the pipeline.

Flags: `--use-existing-coverage`, `--no-coverage`, `--coverage-command`.

## Mutations

Java-style operator mutations plus `??` → `||` on methods with `{ }` or `=>` bodies. Constructors, accessors, and test/generated files are skipped like crapper.

## How C# differs from Java

| Topic | Java | C# |
|-------|------|-----|
| Project marker | nearest **`pom.xml`** | test **`*.csproj`** with **ProjectReference** to the library |
| Default tests | `mvn -q test -DexcludeTags=no-mutate` in the Maven module | `dotnet test Tests.csproj` with **cwd = test project directory** |
| Coverage | **JaCoCo** XML | **Coverlet Cobertura** |
| Filter slow tests | `-DexcludeTags=no-mutate` | no built-in equivalent — use **`--test-command`** |
| Form boundary | method **`block`** | **`block`** or **`=>` expression body** |
| Extra mutations | — | **`??` → `||`** only (not `?.`, `===`, `!==`) |
| Private forms | `private` keyword | same; `internal` / `protected` are not `defn-/` |

## Running mutator

```powershell
cd path\to\mutator
.\.venv\Scripts\python.exe -m mutator --root "D:\path\to\YourSolution" path\to\SomeService.cs
```

Use `--scan`, `--test-command`, `--max-workers`, `--changed`, `--mutate-all` as needed.

Exit **0** / **2** / **3** = all killed / baseline failed / survivor.

Requires **`dotnet`**, Python, and crapper checkout beside mutator.

## Smoke test

```powershell
dotnet test path\to\MyApp.Tests.csproj
.\.venv\Scripts\python.exe -m mutator --root path\to\solution --scan path\to\OneType.cs
.\.venv\Scripts\python.exe -m mutator --root path\to\solution --max-workers 1 path\to\OneType.cs
```

---

[Russian version](csharp-project.ru.md)
