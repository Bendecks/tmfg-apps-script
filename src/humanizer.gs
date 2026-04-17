function humanizeText_(text) {
  if (!text) return text;

  if (Math.random() < 0.4) {
    var openers = [
      "This started out pretty simple.",
      "We didn't plan this at all.",
      "This came from a slightly messy situation.",
      "Not something we thought much about at first.",
      "This was more accidental than planned."
    ];
    text = openers[Math.floor(Math.random() * openers.length)] + " " + text;
  }

  return text;
}

function humanizeSections_(sections) {
  if (!sections || !sections.length) return sections;

  return sections.map(function(s) {
    var text = String(s.p || "");

    if (Math.random() < 0.3) {
      var friction = [
        "At first, this didn't really stick.",
        "Honestly, we almost gave up on this.",
        "It felt like extra work in the beginning.",
        "We forgot to use it the first few days.",
        "It didn't work perfectly right away."
      ];
      text = friction[Math.floor(Math.random() * friction.length)] + " " + text;
    }

    if (Math.random() < 0.25) {
      text = text.replace(/\.$/, "") + ", which helped more than expected.";
    }

    if (Math.random() < 0.2) {
      var details = [
        "Usually right after getting home.",
        "Most days around dinner time.",
        "Especially on the more chaotic days.",
        "When everyone is a bit tired.",
        "On the days where everything feels rushed."
      ];
      text += " " + details[Math.floor(Math.random() * details.length)];
    }

    return {
      h2: s.h2,
      p: text
    };
  });
}
