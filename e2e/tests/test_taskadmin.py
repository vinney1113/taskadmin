import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

scenarios("taskadmin.feature")
scenarios(str(Path(__file__).resolve().parents[2] / "specs" / "kanban" / "kanban.feature"))
scenarios(str(Path(__file__).resolve().parents[2] / "specs" / "figma-design" / "figma-design.feature"))
scenarios(str(Path(__file__).resolve().parents[2] / "specs" / "tasks-rest-api" / "tasks-rest-api.feature"))

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


def api_request(base_url, method, path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as err:
        return err.code, None


def get_tasks(base_url):
    _, tasks = api_request(base_url, "GET", "/api/tasks")
    return tasks or []


def get_projects(base_url):
    _, projects = api_request(base_url, "GET", "/api/projects")
    return projects or []


def make_task(title, start_date=None, status=None, project_id=None):
    task = {"title": title}
    if start_date:
        task["startDate"] = start_date
    if status:
        task["status"] = status
    if project_id:
        task["projectId"] = project_id
    return task


def seed_tasks(driver, base_url, tasks):
    for task in tasks:
        payload = {"title": task["title"]}
        for key in ("startDate", "status", "projectId"):
            if task.get(key):
                payload[key] = task[key]
        status, _ = api_request(base_url, "POST", "/api/tasks", payload)
        assert status == 201, f"failed to seed task {task!r}"
    driver.refresh()
    if tasks:
        wait_for_task_li(driver, tasks[0]["title"])


def task_from_storage(base_url, title):
    for task in get_tasks(base_url):
        if task["title"] == title:
            return task
    return None


def project_id_from_storage(base_url, name):
    for project in get_projects(base_url):
        if project["name"] == name:
            return project["id"]
    return None


def find_li_by_title(driver, title):
    try:
        for li in driver.find_elements(By.CSS_SELECTOR, "#task-list li"):
            spans = li.find_elements(By.CSS_SELECTOR, ".fw-medium")
            if spans and spans[0].text == title:
                return li
    except StaleElementReferenceException:
        return None
    return None


def find_li_by_title_in_column(driver, title, column):
    try:
        for li in driver.find_elements(
            By.CSS_SELECTOR, f"[data-column='{COLUMN_SLUGS[column]}'] li"
        ):
            spans = li.find_elements(By.CSS_SELECTOR, ".fw-medium")
            if spans and spans[0].text == title:
                return li
    except StaleElementReferenceException:
        return None
    return None


def color_of(li):
    try:
        cls = li.get_attribute("class") or ""
        match = re.search(r"text-bg-(\S+)", cls)
        return match.group(1) if match else None
    except StaleElementReferenceException:
        return None


def wait_for_task(driver, title, present=True, timeout=5):
    return WebDriverWait(driver, timeout).until(
        lambda d: (find_li_by_title(d, title) is not None) is present
    )


def wait_for_task_li(driver, title, timeout=10):
    return WebDriverWait(driver, timeout).until(lambda d: find_li_by_title(d, title))


def record_task(driver, context, base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found via API"
    context["created"][task["id"]] = task["createdAt"]
    li = wait_for_task_li(driver, title)
    context["colors"][task["id"]] = color_of(li)


@given(parsers.parse('I have an existing task "{title}"'))
def existing_task(driver, context, base_url, title):
    seed_tasks(driver, base_url, [make_task(title)])
    record_task(driver, context, base_url, title)


@given(parsers.parse('I have an existing task "{title}" with start date "{date}"'))
def existing_task_with_date(driver, context, base_url, title, date):
    seed_tasks(driver, base_url, [make_task(title, start_date=date)])
    record_task(driver, context, base_url, title)


@given(parsers.parse('I have an existing task "{title}" in "In Progress"'))
def existing_task_in_progress(driver, context, base_url, title):
    seed_tasks(driver, base_url, [make_task(title, status="in-progress")])
    record_task(driver, context, base_url, title)


@given(parsers.parse('I have an existing task "{title}" that is completed'))
def existing_task_completed(driver, context, base_url, title):
    seed_tasks(driver, base_url, [make_task(title, status="completed")])
    record_task(driver, context, base_url, title)


@given(parsers.parse('I have existing tasks "{t1}" and "{t2}"'))
def existing_tasks(driver, context, base_url, t1, t2):
    seed_tasks(driver, base_url, [make_task(t1), make_task(t2)])
    record_task(driver, context, base_url, t1)
    record_task(driver, context, base_url, t2)


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
    li = wait_for_task_li(driver, old)
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    li.find_element(By.CSS_SELECTOR, "button[data-action='save']").click()


@when(parsers.re(r'I edit the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)" without saving'))
def edit_task_without_saving(driver, old, new):
    li = wait_for_task_li(driver, old)
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)


@when(parsers.re(r'I start editing the task "(?P<title>[^"]*)"'))
def start_editing_task(driver, title):
    li = wait_for_task_li(driver, title)
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
    li = wait_for_task_li(driver, old)
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    inp.send_keys(Keys.ENTER)


@when(parsers.re(r'I press Escape while editing the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)"'))
def press_escape_while_editing(driver, old, new):
    li = wait_for_task_li(driver, old)
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    inp.send_keys(Keys.ESCAPE)


@when(parsers.re(r'I cancel editing the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)"'))
def cancel_editing(driver, old, new):
    li = wait_for_task_li(driver, old)
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    li.find_element(By.CSS_SELECTOR, "button[data-action='cancel']").click()


@when(parsers.parse('I mark "{title}" as completed'))
def mark_completed(driver, title):
    li = wait_for_task_li(driver, title)
    checkbox = li.find_element(By.CSS_SELECTOR, "input[data-action='toggle']")
    if not checkbox.is_selected():
        checkbox.click()


@when(parsers.parse('I delete the task "{title}"'))
def delete_task(driver, title):
    li = wait_for_task_li(driver, title)
    li.find_element(By.CSS_SELECTOR, "button[data-action='delete']").click()
    WebDriverWait(driver, 5).until(EC.alert_is_present())
    driver.switch_to.alert.accept()


@when(parsers.parse('I move the task "{title}" to "{column}"'))
def move_task(driver, title, column):
    li = wait_for_task_li(driver, title)
    target = driver.find_element(
        By.CSS_SELECTOR, f"[data-column='{COLUMN_SLUGS[column]}']"
    )
    driver.execute_script(DRAG_TO_COLUMN_JS, li, target)


@when(parsers.parse('I unmark "{title}" as completed'))
def unmark_completed(driver, title):
    li = wait_for_task_li(driver, title)
    checkbox = li.find_element(By.CSS_SELECTOR, "input[data-action='toggle']")
    if checkbox.is_selected():
        checkbox.click()


@given("I have an existing task with a double-quoted title")
def existing_quoted_task(driver, context, base_url):
    seed_tasks(driver, base_url, [make_task(QUOTED_TITLE)])
    record_task(driver, context, base_url, QUOTED_TITLE)


@when("I start editing that task")
def start_editing_quoted(driver):
    li = wait_for_task_li(driver, QUOTED_TITLE)
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
    li = wait_for_task_li(driver, title)
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
def title_remains(driver, base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert task["title"] == title


@then(parsers.parse('the task "{title}" remains completed'))
def remains_completed(driver, base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert task["status"] == "completed"


@then(parsers.parse('the task "{title}" keeps its original creation date'))
def keeps_created_date(driver, context, base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert task["createdAt"] == context["created"][task["id"]]


@then(parsers.parse('the task "{title}" shows start date "{date}"'))
def shows_start_date(driver, base_url, title, date):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert task["startDate"] == date


@then(parsers.parse('the task "{title}" keeps its start date "{date}"'))
def keeps_start_date(driver, base_url, title, date):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert task["startDate"] == date


@then(parsers.parse('the task "{title}" has no start date'))
def has_no_start_date(driver, base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert not task.get("startDate")


@then(parsers.parse('the task "{title}" is assigned a color'))
def assigned_color(driver, title):
    li = wait_for_task_li(driver, title)
    assert color_of(li), f"task {title!r} has no color"


@then(parsers.parse('the task "{title}" keeps its color'))
@then(parsers.parse('the task "{title}" keeps its original color'))
def keeps_color(driver, context, base_url, title):
    li = wait_for_task_li(driver, title)
    task = task_from_storage(base_url, title)
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
    try:
        for card in driver.find_elements(By.CSS_SELECTOR, "#task-groups-list .task-group-card"):
            if card.get_attribute("data-project") == name:
                return card
    except StaleElementReferenceException:
        return None
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


def home_progress_visible(driver, percent):
    return driver.find_element(By.ID, "progress-percent").text == percent


@then(parsers.parse('the home header shows the progress "{percent}"'))
def home_header_progress(driver, percent):
    WebDriverWait(driver, 10).until(lambda d: home_progress_visible(d, percent))


@given(parsers.parse('I have existing tasks "{t1}" and "{t2}" in project "{project}"'))
def existing_tasks_in_project(driver, context, base_url, t1, t2, project):
    pid = project_id_from_storage(base_url, project)
    assert pid is not None, f"project {project!r} not found via API"
    seed_tasks(
        driver,
        base_url,
        [make_task(t1, project_id=pid), make_task(t2, project_id=pid)],
    )
    record_task(driver, context, base_url, t1)
    record_task(driver, context, base_url, t2)


@given(parsers.parse('"{title}" is completed'))
def task_is_completed(driver, base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found via API"
    status, _ = api_request(
        base_url, "PUT", f"/api/tasks/{task['id']}", {"status": "completed"}
    )
    assert status == 200
    driver.refresh()
    wait_for_task_li(driver, title)


def group_count_visible(driver, project, count):
    card = find_group_card(driver, project)
    if card is None:
        return False
    meta = card.find_element(By.CSS_SELECTOR, ".task-group-meta")
    return meta.text.split()[0] == count


@then(parsers.parse('the task group "{project}" shows "{count}" tasks'))
def group_shows_count(driver, project, count):
    WebDriverWait(driver, 10).until(lambda d: group_count_visible(d, project, count))


def group_progress_visible(driver, project, percent):
    card = find_group_card(driver, project)
    if card is None:
        return False
    el = card.find_element(By.CSS_SELECTOR, ".task-group-count")
    return el.text == percent


@then(parsers.parse('the task group "{project}" shows "{percent}" progress'))
def group_shows_progress(driver, project, percent):
    WebDriverWait(driver, 10).until(lambda d: group_progress_visible(d, project, percent))


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


def group_card_present(driver, name):
    return find_group_card(driver, name) is not None


@then(parsers.parse('a task group "{name}" appears on the home screen'))
def group_appears(driver, name):
    WebDriverWait(driver, 5).until(lambda d: group_card_present(d, name))


@given("the API is running against an empty database")
def api_empty_database(base_url):
    for task in get_tasks(base_url):
        api_request(base_url, "DELETE", f"/api/tasks/{task['id']}")
    for project in get_projects(base_url):
        api_request(base_url, "DELETE", f"/api/projects/{project['id']}")


@when(parsers.re(r'I POST a task with title "(?P<title>[^"]*)"'))
def api_post_task(base_url, context, title):
    context["last"] = api_request(base_url, "POST", "/api/tasks", {"title": title})


@when(parsers.re(r'I POST a task with title "(?P<title>[^"]*)" and status "(?P<status>[^"]*)"'))
def api_post_task_with_status(base_url, context, title, status):
    context["last"] = api_request(
        base_url, "POST", "/api/tasks", {"title": title, "status": status}
    )


@given(parsers.re(r'a task "(?P<title>[^"]*)" exists'))
def api_task_exists(base_url, context, title):
    status, body = api_request(base_url, "POST", "/api/tasks", {"title": title})
    assert status == 201
    context["last_task_id"] = body["id"]


@when("I GET the tasks")
def api_get_tasks(base_url, context):
    context["last"] = api_request(base_url, "GET", "/api/tasks")


@then(parsers.parse('the response contains tasks "{t1}" and "{t2}"'))
def api_contains_tasks(context, t1, t2):
    titles = [t["title"] for t in context["last"][1]]
    assert t1 in titles and t2 in titles, titles


@when("I GET that task")
def api_get_that_task(base_url, context):
    context["last"] = api_request(
        base_url, "GET", f"/api/tasks/{context['last_task_id']}"
    )


@when(parsers.parse('I GET a task with id "{tid}"'))
def api_get_task_by_id(base_url, context, tid):
    context["last"] = api_request(base_url, "GET", f"/api/tasks/{tid}")


@when(parsers.re(r'I PUT that task with title "(?P<title>[^"]*)" and status "(?P<status>[^"]*)"'))
def api_put_that_task(base_url, context, title, status):
    context["last"] = api_request(
        base_url,
        "PUT",
        f"/api/tasks/{context['last_task_id']}",
        {"title": title, "status": status},
    )


@when("I DELETE that task")
def api_delete_that_task(base_url, context):
    context["last"] = api_request(
        base_url, "DELETE", f"/api/tasks/{context['last_task_id']}"
    )


@then(parsers.parse('GET the tasks does not include "{title}"'))
def api_tasks_exclude(base_url, title):
    titles = [t["title"] for t in get_tasks(base_url)]
    assert title not in titles, titles


@given(parsers.parse('a project "{name}" exists'))
def api_project_exists(base_url, context, name):
    status, body = api_request(base_url, "POST", "/api/projects", {"name": name})
    assert status == 201
    context["last_project_id"] = body["id"]


@when(parsers.parse('I POST a project with name "{name}"'))
def api_post_project(base_url, context, name):
    context["last"] = api_request(base_url, "POST", "/api/projects", {"name": name})


@then(parsers.parse('the response project has name "{name}"'))
def api_project_name(context, name):
    assert context["last"][1]["name"] == name


@given(parsers.re(r'a task "(?P<title>[^"]*)" assigned to "(?P<project>[^"]*)" exists'))
def api_task_in_project(base_url, context, title, project):
    pid = project_id_from_storage(base_url, project)
    assert pid is not None, f"project {project!r} not found"
    status, body = api_request(
        base_url, "POST", "/api/tasks", {"title": title, "projectId": pid}
    )
    assert status == 201
    context["last_task_id"] = body["id"]


@when("I DELETE that project")
def api_delete_that_project(base_url, context):
    context["last"] = api_request(
        base_url, "DELETE", f"/api/projects/{context['last_project_id']}"
    )


@then(parsers.parse('the task "{title}" has no project'))
def api_task_no_project(base_url, title):
    task = task_from_storage(base_url, title)
    assert task is not None, f"task {title!r} not found"
    assert task["projectId"] is None


@then(parsers.re(r'the response status is (?P<status>\d+)'))
def api_response_status(context, status):
    assert context["last"][0] == int(status), context["last"]


@then(parsers.parse('the response task has title "{title}"'))
def api_task_title(context, title):
    assert context["last"][1]["title"] == title


@then(parsers.parse('the response task has status "{status}"'))
def api_task_status(context, status):
    assert context["last"][1]["status"] == status
