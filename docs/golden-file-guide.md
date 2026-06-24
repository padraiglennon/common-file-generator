# Preparing a "Golden" template file

A **Golden file** is an ordinary PowerPoint, Word, or Excel file that you design
to look exactly the way you want - colours, fonts, logos, layout, charts. The
tool never changes the design; it only drops your data into the spots you mark.

You mark those spots with **tags**. This guide shows how, with no programming.

---

## PowerPoint (`.pptx`)

### Text spots

Type a tag where you want text to appear, using double curly braces:

```
{{title}}
{{author}}
```

When you run the tool, `{{title}}` is replaced by the `title` value from your
data file. The surrounding formatting (font, size, colour) is kept.

### Tables

1. Insert a table and style it as you like.
2. Give the table a **name** so the tool can find it:
   - Select the table.
   - On the **Home** tab, open the **Selection Pane** (Arrange ▸ Selection Pane).
   - Double-click the table's entry and rename it, e.g. `RevenueTable`.
3. Use that same name in the `tables` section of your data file.

The tool fills the existing cells top-to-bottom; if you have a header row in the
template, send your data without a header (or use the `header` field - your call).

### Pictures

1. Draw a rectangle (or any shape) where the picture should go, at the size you
   want.
2. Open the **Selection Pane** and rename that shape, e.g. `Logo`.
3. Reference `Logo` in the `media` section of your data file. The shape is
   replaced by your image at the same position and size.

---

## Word (`.docx`)

Word has no Selection Pane for naming, so you mark elements with tags typed
**into the document**:

- **Text:** type `{{author}}` where the text should go.
- **Tables:** click into any cell of the table and type `{{table:RevenueTable}}`.
  That cell's marker names the whole table `RevenueTable`. (Put it in a cell you
  will overwrite with data, or a spare cell.)
- **Pictures:** on its own line, type `{{media:Logo}}`. It is replaced by the
  image.

Use the same names (`RevenueTable`, `Logo`) in your data file.

---

## Excel (`.xlsx`)

Excel uses **defined names** (built-in to Excel) as tags:

1. Select the cell (for text or a picture) or the **top-left** cell of a table
   area.
2. Go to **Formulas ▸ Name Manager ▸ New** (or type a name in the Name Box to
   the left of the formula bar).
3. Give it a name, e.g. `title`, `RevenueTable`, or `Logo`.

Then in your data file:

- a `text` entry named `title` writes into that single cell;
- a `tables` entry named `RevenueTable` fills rows **down and right** from the
  anchor cell, using the cells that already exist on the sheet;
- a `media` entry named `Logo` anchors the picture to that cell.

---

## Rules of thumb

- **Names are how the data finds its spot** - keep them identical in the
  template and the data file (they are case-sensitive).
- **Design lives in the template, data lives in the JSON** - never the other way
  around.
- **Leave room** - the tool fills existing cells/shapes; it does not grow tables
  or add slides. If your data is bigger than the template, the extra is skipped
  and the report file tells you.
