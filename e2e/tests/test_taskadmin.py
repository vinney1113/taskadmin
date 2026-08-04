import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

scenarios("taskadmin.feature")
scenarios(str(Path(__file__).resolve().parents[2] / "specs" / "kanban" / "kanban.feature"))
scenarios(str(Path(__file__).resolve().parents[2] / "specs" / "figma-design" / "figma-design.feature"))

QUOTED_TITLE = 'Buy "milk" & eggs'

COLUMN_SLUGS = {
    "Prioritize": "prioritize",
    "In Progress": "in-progress",
    "Completed": "completed",
}

DRAG_TO_COLUMN_JS = """
function dragToColumn(source, target) {
  const dataTransfer = new DataTransfer();
  source.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, dataTransfer }));
  target.dispatchEvent(new DragEvent('dragenter', { bubbles: true, cancelable: true, dataTransfer }));
  target.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer }));
  target.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer }));
  source.dispatchEvent(new DragEvent('dragend', { bubbles: true, cancelable: true, dataTransfer }));
}
dragToColumn(arguments[0], arguments[1]);
"""


def make_task(title, start_date=None, status=None, project_id=None):
    task = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, title)),
        "title": title,
        "createdAt": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "startDate": start_date,
        "projectId": project_id,
    }
    if status is not None:
        task["status"] = status
    return task


def project_id_from_storage(driver, name):
    projects = driver.execute_script(
        "return JSON.parse(localStorage.getItem('projects') || '[]');"
    )
    for project in projects:
        if project["name"] == name:
            return project["id"]
    return None


def seed_tasks(driver, tasks):
    driver.execute_script(
        "localStorage.setItem('tasks', arguments[0]);",
        json.dumps(tasks),
    )
    driver.refresh()


def task_from_storage(driver, title):
    tasks = driver.execute_script(
        "return JSON.parse(localStorage.getItem('tasks') || '[]');"
    )
    for task in tasks:
        if task["title"] == title:
            return task
    return None


def find_li_by_title(driver, title):
    for li in driver.find_elements(By.CSS_SELECTOR, "#task-list li"):
        spans = li.find_elements(By.CSS_SELECTOR, ".fw-medium")
        if spans and spans[0].text == title:
            return li
    return None


def find_li_by_title_in_column(driver, title, column):
    for li in driver.find_elements(
        By.CSS_SELECTOR, f"[data-column='{COLUMN_SLUGS[column]}'] li"
    ):
        spans = li.find_elements(By.CSS_SELECTOR, ".fw-medium")
        if spans and spans[0].text == title:
            return li
    return None


def color_of(li):
    cls = li.get_attribute("class") or ""
    match = re.search(r"text-bg-(\S+)", cls)
    return match.group(1) if match else None


def wait_for_task(driver, title, present=True, timeout=5):
    return WebDriverWait(driver, timeout).until(
        lambda d: (find_li_by_title(d, title) is not None) is present
    )


def record_task(driver, context, title):
    task = task_from_storage(driver, title)
    context["created"][task["id"]] = task["createdAt"]
    li = find_li_by_title(driver, title)
    context["colors"][task["id"]] = color_of(li)


@given(parsers.parse('I have an existing task "{title}"'))
def existing_task(driver, context, title):
    seed_tasks(driver, [make_task(title)])
    record_task(driver, context, title)


@given(parsers.parse('I have an existing task "{title}" with start date "{date}"'))
def existing_task_with_date(driver, context, title, date):
    seed_tasks(driver, [make_task(title, start_date=date)])
    record_task(driver, context, title)


@given(parsers.parse('I have an existing task "{title}" in "In Progress"'))
def existing_task_in_progress(driver, context, title):
    seed_tasks(driver, [make_task(title, status="in-progress")])
    record_task(driver, context, title)


@given(parsers.parse('I have an existing task "{title}" that is completed'))
def existing_task_completed(driver, context, title):
    seed_tasks(driver, [make_task(title, status="completed")])
    record_task(driver, context, title)


@given(parsers.parse('I have existing tasks "{t1}" and "{t2}"'))
def existing_tasks(driver, context, t1, t2):
    seed_tasks(driver, [make_task(t1), make_task(t2)])
    record_task(driver, context, t1)
    record_task(driver, context, t2)


@given(parsers.parse('I enter the task title "{title}"'))
def enter_title(driver, title):
    el = driver.find_element(By.ID, "title")
    el.clear()
    el.send_keys(title)


@given(parsers.parse('I set the start date to "{date}"'))
def set_start_date(driver, date):
    driver.execute_script(
        "document.getElementById('start-date').value = arguments[0];",
        date,
    )


@given("I leave the start date empty")
def leave_date_empty(driver):
    driver.find_element(By.ID, "start-date").clear()


@when("I submit the task")
def submit_task(driver):
    driver.find_element(By.CSS_SELECTOR, "#task-form button[type='submit']").click()


@when(parsers.parse('I create a task "{title}"'))
def create_task(driver, title):
    driver.find_element(By.ID, "title").send_keys(title)
    driver.find_element(By.CSS_SELECTOR, "#task-form button[type='submit']").click()


@when(parsers.re(r'I edit the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)"'))
def edit_task(driver, old, new):
    li = find_li_by_title(driver, old)
    assert li is not None, f"task {old!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    li.find_element(By.CSS_SELECTOR, "button[data-action='save']").click()


@when(parsers.re(r'I edit the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)" without saving'))
def edit_task_without_saving(driver, old, new):
    li = find_li_by_title(driver, old)
    assert li is not None, f"task {old!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)


@when(parsers.re(r'I start editing the task "(?P<title>[^"]*)"'))
def start_editing_task(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )


@when("I cancel the current edit")
def cancel_current_edit(driver):
    driver.find_element(By.CSS_SELECTOR, "button[data-action='cancel']").click()


@then("no error message is shown")
def no_error_shown(driver):
    err = driver.find_element(By.ID, "error")
    assert not err.is_displayed(), "error element is still visible"


@when(parsers.re(r'I edit the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)" with Enter'))
def edit_task_with_enter(driver, old, new):
    li = find_li_by_title(driver, old)
    assert li is not None, f"task {old!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    inp.send_keys(Keys.ENTER)


@when(parsers.re(r'I press Escape while editing the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)"'))
def press_escape_while_editing(driver, old, new):
    li = find_li_by_title(driver, old)
    assert li is not None, f"task {old!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    inp.send_keys(Keys.ESCAPE)


@when(parsers.re(r'I cancel editing the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)"'))
def cancel_editing(driver, old, new):
    li = find_li_by_title(driver, old)
    assert li is not None, f"task {old!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    li.find_element(By.CSS_SELECTOR, "button[data-action='cancel']").click()


@when(parsers.parse('I mark "{title}" as completed'))
def mark_completed(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not found"
    checkbox = li.find_element(By.CSS_SELECTOR, "input[data-action='toggle']")
    if not checkbox.is_selected():
        checkbox.click()


@when(parsers.parse('I delete the task "{title}"'))
def delete_task(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='delete']").click()
    driver.switch_to.alert.accept()


@when(parsers.parse('I move the task "{title}" to "{column}"'))
def move_task(driver, title, column):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not found"
    target = driver.find_element(
        By.CSS_SELECTOR, f"[data-column='{COLUMN_SLUGS[column]}']"
    )
    driver.execute_script(DRAG_TO_COLUMN_JS, li, target)


@when(parsers.parse('I unmark "{title}" as completed'))
def unmark_completed(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not found"
    checkbox = li.find_element(By.CSS_SELECTOR, "input[data-action='toggle']")
    if checkbox.is_selected():
        checkbox.click()


@given("I have an existing task with a double-quoted title")
def existing_quoted_task(driver, context):
    seed_tasks(driver, [make_task(QUOTED_TITLE)])
    record_task(driver, context, QUOTED_TITLE)


@when("I start editing that task")
def start_editing_quoted(driver):
    li = find_li_by_title(driver, QUOTED_TITLE)
    assert li is not None, f"task {QUOTED_TITLE!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )


@then("the edit field shows the full double-quoted title")
def edit_field_shows_full_title(driver):
    inp = driver.find_element(By.CSS_SELECTOR, ".edit-input")
    assert inp.get_attribute("value") == QUOTED_TITLE


@then(parsers.parse('the task "{title}" is marked as completed'))
def is_marked_completed(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not in list"
    checkbox = li.find_element(By.CSS_SELECTOR, "input[data-action='toggle']")
    assert checkbox.is_selected(), f"task {title!r} is not completed"


@then(parsers.parse('the task list shows "{title}"'))
def list_shows(driver, title):
    assert wait_for_task(driver, title), f"task {title!r} not in list"


@then(parsers.parse('the task list should show "{title}"'))
def list_should_show(driver, title):
    assert wait_for_task(driver, title), f"task {title!r} not in list"


@then(parsers.parse('the task list should not show "{title}"'))
def list_should_not_show(driver, title):
    assert wait_for_task(driver, title, present=False), f"task {title!r} still in list"


@then("an error message is shown")
def error_shown(driver):
    err = driver.find_element(By.ID, "error")
    assert err.is_displayed(), "error element is not visible"
    assert err.text.strip(), "error element has no message"


@then(parsers.parse('the task title remains "{title}"'))
def title_remains(driver, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["title"] == title


@then(parsers.parse('the task "{title}" remains completed'))
def remains_completed(driver, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["status"] == "completed"


@then(parsers.parse('the task "{title}" keeps its original creation date'))
def keeps_created_date(driver, context, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["createdAt"] == context["created"][task["id"]]


@then(parsers.parse('the task "{title}" shows start date "{date}"'))
def shows_start_date(driver, title, date):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["startDate"] == date


@then(parsers.parse('the task "{title}" keeps its start date "{date}"'))
def keeps_start_date(driver, title, date):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["startDate"] == date


@then(parsers.parse('the task "{title}" has no start date'))
def has_no_start_date(driver, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert not task.get("startDate")


@then(parsers.parse('the task "{title}" is assigned a color'))
def assigned_color(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not in list"
    assert color_of(li), f"task {title!r} has no color"


@then(parsers.parse('the task "{title}" keeps its color'))
@then(parsers.parse('the task "{title}" keeps its original color'))
def keeps_color(driver, context, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not in list"
    task = task_from_storage(driver, title)
    assert color_of(li) == context["colors"][task["id"]]


@then("no two tasks share the same color")
def unique_colors(driver):
    colors = [
        color_of(li)
        for li in driver.find_elements(By.CSS_SELECTOR, "#task-list li")
    ]
    assert len(colors) == len(set(colors)), f"duplicate colors found: {colors}"


@then(parsers.re(r'the task "(?P<title>[^"]*)" is in the (?P<column>Prioritize|In Progress|Completed) column'))
def task_in_column(driver, title, column):
    WebDriverWait(driver, 5).until(
        lambda d: find_li_by_title_in_column(d, title, column) is not None
    )


@then(parsers.re(r'the task "(?P<title>[^"]*)" is not in the (?P<column>Prioritize|In Progress|Completed) column'))
def task_not_in_column(driver, title, column):
    WebDriverWait(driver, 5).until(
        lambda d: find_li_by_title_in_column(d, title, column) is None
    )


@then(parsers.re(r'the (?P<column>Prioritize|In Progress|Completed) column does not show "(?P<title>[^"]*)"'))
def column_not_show(driver, column, title):
    WebDriverWait(driver, 5).until(
        lambda d: find_li_by_title_in_column(d, title, column) is None
    )


@then(parsers.parse('the board shows the columns "{c1}", "{c2}", and "{c3}"'))
def board_shows_columns(driver, c1, c2, c3):
    headings = [
        h.text
        for h in driver.find_elements(By.CSS_SELECTOR, "#task-list .kanban-heading")
    ]
    assert headings == [c1, c2, c3], f"columns mismatch: {headings}"


def page_font(driver):
    return driver.execute_script(
        "return getComputedStyle(document.body).fontFamily;"
    )


def page_bg(driver):
    return driver.execute_script(
        "return getComputedStyle(document.body).backgroundColor;"
    )


def primary_color(driver):
    return driver.execute_script(
        "return getComputedStyle(document.documentElement)"
        ".getPropertyValue('--primary').trim();"
    )


def find_group_card(driver, name):
    for card in driver.find_elements(By.CSS_SELECTOR, "#task-groups-list .task-group-card"):
        if card.get_attribute("data-project") == name:
            return card
    return None


FILTER_SLUGS = {
    "All": "all",
    "To do": "to-do",
    "In Progress": "in-progress",
    "Completed": "completed",
}


@then("the page uses the Manrope font family")
def uses_manrope(driver):
    assert "Manrope" in page_font(driver), f"font is {page_font(driver)!r}"


@given("the app is open")
def app_is_open(driver):
    pass


@then("the page uses the design's purple accent color")
def uses_purple(driver):
    assert primary_color(driver).lower() == "#5f33e1", primary_color(driver)


@then("the page background is the design's light color")
def uses_light_background(driver):
    bg = page_bg(driver)
    assert bg == "rgb(240, 240, 240)", f"background is {bg!r}"


@then(parsers.parse('the home header shows "{text}"'))
def home_header_shows(driver, text):
    el = driver.find_element(By.CSS_SELECTOR, ".home-title")
    assert el.text == text, f"header text is {el.text!r}"


@then(parsers.parse('the home header shows the progress "{percent}"'))
def home_header_progress(driver, percent):
    el = driver.find_element(By.ID, "progress-percent")
    assert el.text == percent, f"progress is {el.text!r}"


@given(parsers.parse('I have existing tasks "{t1}" and "{t2}" in project "{project}"'))
def existing_tasks_in_project(driver, context, t1, t2, project):
    pid = project_id_from_storage(driver, project)
    assert pid is not None, f"project {project!r} not found in storage"
    seed_tasks(
        driver,
        [make_task(t1, project_id=pid), make_task(t2, project_id=pid)],
    )
    record_task(driver, context, t1)
    record_task(driver, context, t2)


@given(parsers.parse('"{title}" is completed'))
def task_is_completed(driver, title):
    tasks = json.loads(
        driver.execute_script("return localStorage.getItem('tasks') || '[]';")
    )
    for task in tasks:
        if task["title"] == title:
            task["status"] = "completed"
    driver.execute_script(
        "localStorage.setItem('tasks', arguments[0]);",
        json.dumps(tasks),
    )
    driver.refresh()


@then(parsers.parse('the task group "{project}" shows "{count}" tasks'))
def group_shows_count(driver, project, count):
    card = find_group_card(driver, project)
    assert card is not None, f"group {project!r} not found"
    assert card.find_element(By.CSS_SELECTOR, ".task-group-meta").text.split()[0] == count


@then(parsers.parse('the task group "{project}" shows "{percent}" progress'))
def group_shows_progress(driver, project, percent):
    card = find_group_card(driver, project)
    assert card is not None, f"group {project!r} not found"
    assert card.find_element(By.CSS_SELECTOR, ".task-group-count").text == percent


@when(parsers.parse('I filter tasks by "{chip}"'))
def filter_tasks(driver, chip):
    slug = FILTER_SLUGS[chip]
    driver.find_element(By.CSS_SELECTOR, f"[data-filter='{slug}']").click()


@then(parsers.parse('the board shows "{title}"'))
def board_shows(driver, title):
    assert wait_for_task(driver, title), f"task {title!r} not in board"


@then(parsers.parse('the board does not show "{title}"'))
def board_does_not_show(driver, title):
    assert wait_for_task(driver, title, present=False), f"task {title!r} still in board"


@given("I open the Add Project form")
def open_add_project(driver):
    driver.find_element(By.ID, "add-project-btn").click()


@when(parsers.parse('I add a project named "{name}"'))
def add_project(driver, name):
    driver.find_element(By.ID, "project-name").send_keys(name)
    driver.find_element(By.ID, "project-form").submit()


@then(parsers.parse('a task group "{name}" appears on the home screen'))
def group_appears(driver, name):
    WebDriverWait(driver, 5).until(lambda d: find_group_card(d, name) is not None)
