// TODO: pass this as an object
function initSurvey(survey_name, survey, submit_button) {
  var extendable_checkbox_lists = [];
  var ecl_divs = survey.querySelectorAll('div.checkboxes.extendable');
  for (var i = 0, ec; ec = ecl_divs[i++];) {
    extendable_checkbox_lists.push(ec.querySelector('[type=checkbox]').name);
  }

  // suppress conventional form submission
  survey.addEventListener('submit', function(e) { e.preventDefault(); });

  // submit form as JSON
  var events = ['click', 'keypress'];
  for (var i = 0, e; e = events[i++];) {
    submit_button.addEventListener(e, function() {
      var json = {};
      for (var i = 0, field; field = fields[i++];) {
        if (field.name != undefined && field.name != '') {
          if (field.name.substr(-2) === '[]') { // checkbox
            json[field.name] = json[field.name] || []; // instantiate as array if needed
            if (field.checked) { json[field.name].push(field.value); }
          } else {
            json[field.name] = field.value;
          }
        }
      }

      var data = JSON.stringify({ 'content': json, 'survey_name': survey_name });
      var xhr = new XMLHttpRequest();
      xhr.open('POST', '/submit', true);
      xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      xhr.onload = function() {
        if (this.status === 200) {
          window.location = this.responseText; // redirect to where we're told
        } else {
          console.log(data);
          alert("Keanu 'Whoa' " + this.status + " error; and that's not supposed to happen."
          + "\n\nWould you please report this error at"
          +   "\nhttps://github.com/psychoinformatics-de/dmc/issues");
        }
      };
      xhr.send(data);
    });
  }

  // TODO: would be nice if "fields" wasn't a global var.
  // fields, upon completion/validation, will show/scroll-to the next question
  for (var i = 0, f; f = fields[i++];) {
    if (f.nodeName == 'SELECT') {
      f.addEventListener('change', watchIfReadyForNextQuestion);
    } else if (f.nodeName == 'INPUT') {
      if (f.type == 'checkbox') {
        if (extendable_checkbox_lists.indexOf(f.name) < 0) { // skip over extendable checkboxes
          f.addEventListener('change', watchIfReadyForNextQuestion);
        }
      } else if (f.type !== 'hidden') {
        f.addEventListener('input', watchIfReadyForNextQuestion);
      }
    }
  }

  // clone previous label/checkbox; insert
  function extendCheckboxList(el) {
    var val = el.value.trim();
    if (val != '') {
      var newCbox = el.parentNode.previousElementSibling.cloneNode(true);
      newCbox.firstChild.checked = true; newCbox.firstChild.value = val;
      newCbox.lastChild.data = ' ' + val;
      el.parentNode.parentNode.insertBefore(newCbox, el.parentNode);
    }
    el.value = '';
  }

  // TODO: it might just be better to have the HTML in the doc to begin with.
  // build and insert extendable checkbox input field and "next" button
  for (var i = 0, ec; ec = extendable_checkbox_lists[i++];) {
    var panel = getPanel(fields[ec]);
    var l = document.createElement('label');
    var c = document.createElement('input'); c.type = 'checkbox'; c.disabled = true;
    var t = document.createElement('input'); t.type = 'text'; t.placeholder = 'anderes (+ fügt hinzu)';
        t.classList.add('extend');
        t.onkeydown = function(e) { e.keyCode == 13 && extendCheckboxList(this); };
    var a = document.createElement('a'); a.tabIndex = '0'; a.classList.add('icon-plus', 'button');
      var events = ['click', 'keypress'];
      for (var j = 0, e; e = events[j++];) {
        a.addEventListener(e, function() { extendCheckboxList(this.previousElementSibling); });
      }

    l.appendChild(c); l.appendChild(t); l.appendChild(a);
    panel.querySelector('.checkboxes.extendable').appendChild(l);

    var button = document.createElement('a');
    button.classList.add('button');
    button.tabIndex = 0;
    button.innerHTML = "<i class='icon-right-open'></i>N&auml;chste Frage";

    var events = ['click', 'keypress'];
    for (var j = 0, e; e = events[j++];) {
      button.addEventListener(e, function() {
        extendCheckboxList(getPanel(this).querySelector('input.extend'));
        markValid(this);
        scrollToNextPanel(this);
      });
    }

    panel.appendChild(button);
  }
}

// easing functions http://goo.gl/5HLl8
Math.easeInOutQuad = function(t, b, c, d) {
  t /= d/2;
  if (t < 1) {
    return c/2*t*t + b
  }
  t--;
  return -c/2 * (t*(t-2) - 1) + b;
};

// the user should win over the scrollTo() animation
scrolling = undefined;
function scrollStop() {
  cancelAnimationFrame(scrolling);
  var events = ['mousedown', 'wheel', 'touchmove'];
  for (var i = 0, e; e = events[i++];) {
    document.querySelector('html').removeEventListener(e, scrollStop);
  }
}
function scrollTo(to, duration) {
  // bail on IE (but not Edge); the auto-scrolling doesn't work well there
  if (window.navigator.userAgent.indexOf('Trident') > 0) { return true; }

  // because it's so fucking difficult to detect the scrolling element, just move them all
  // "someday" document.scrollingElement can be used instead.
  function move(amount) {
    document.documentElement.scrollTop = amount;
    document.body.parentNode.scrollTop = amount;
    document.body.scrollTop = amount;
  }
  function position() {
    return document.documentElement.scrollTop || document.body.parentNode.scrollTop || document.body.scrollTop;
  }
  function getOffset(el) {
    return el.getBoundingClientRect().top + window.scrollY;
  }

  var events = ['mousedown', 'wheel', 'touchmove'];
  for (var i = 0, e; e = events[i++];) {
    document.querySelector('html').addEventListener(e, scrollStop);
  }

  var start = position(),
    dest = getOffset(to) - start,
    currentTime = 0,
    increment = 20;

  var animateScroll = function() {
    currentTime += increment;
    move(Math.easeInOutQuad(currentTime, start, dest, duration));
    if (currentTime < duration) { // animate unless finished
      scrolling = requestAnimationFrame(animateScroll);
    } else {
      scrollStop();
    }
  };
  scrolling = animateScroll();
}

/*
 *  Mark question as valid or invalid
 */
function markInvalid(el) {
  var panel = getPanel(el);

  panel.classList.remove('badge-success');
  panel.classList.add('has-error');

  var error_box = panel.querySelector('div.error-box');
  if (error_box == null) {
    error_box = document.createElement('div');
    error_box.classList.add('error-box');
    panel.appendChild(error_box);
  }

  var message = ''
  var panel_fields = panel.querySelectorAll('input,select');
  for (var i = 0, f; f = panel_fields[i++];) {
    if (f.validationMessage != undefined) {
      message += f.validationMessage;
    }
  }
  error_box.textContent = message;
}

function markValid(el) {
  var panel = getPanel(el);

  panel.classList.remove('has-error');
  panel.classList.add('badge-success');

  var error_box = panel.querySelector('div.error-box');
  if (error_box !== null) {
    panel.removeChild(error_box);
  }
}

function nextPanel(el) {
  var panel = getPanel(el);
  var next = panel.dataset.nextPanel;

  if (next == undefined) { // if none, then simply go to next in DOM
    return panel.nextElementSibling;
  } else {
    return getPanel(fields[next]);
  }
}

function scrollToNextPanel(el) {
  var next_panel = nextPanel(el);
  showPanel(next_panel);
  scrollTo(next_panel, 3000);
  next_panel.querySelector('input,select,a.button').focus();
}

// event = fired from onchange/input event
// TODO: holy hell this name is long...
function watchIfReadyForNextQuestion(event) {
  var field = event.target;
  var panel = getPanel(field);
  var timer = 0;

  if (field.nodeName == 'SELECT') {
    timer = 500;
  } else if (field.nodeName == 'INPUT') {
    switch (field.getAttribute('type')) {
      case 'checkbox':
        timer = 2000; break;
      case 'text':
        timer = 1500; break;
      default:
        timer = 1000;
    }
  }

  clearTimeout(panel.timer);
  panel.timer = setTimeout(function() {
    panel.timer = undefined;

    if (field.nodeName == 'A' || field.validity.valid) {
      try { field.postValidation(); } catch(e) { /* pass */ }

      markValid(panel);
      scrollToNextPanel(panel);
    } else {
      markInvalid(panel);
    }
  }, timer);
}

// get the parent panel of an element
function getPanel(el) {
  var el = el.nodeName ? el : el[0]; // if a list, choose first item
  while (el !== document) {
    if (el.classList.contains('tl-panel')) { return el; } else { el = el.parentNode; }
  }
  return null;
};

// hide the panel(s) (or parent panel(s) of the passed element(s))
function hidePanel() {
  for (var i = 0; i < arguments.length; i++) {
    var panel = getPanel(arguments[i]);
    panel.classList.remove('visible');
  }
}
// show the panel(s) (or parent panel(s) of the passed element(s))
function showPanel() {
  for (var i = 0; i < arguments.length; i++) {
    var panel = getPanel(arguments[i]);
    panel.classList.add('visible');
  }
}
