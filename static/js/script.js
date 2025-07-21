/**
 * Utility function to create a styled section/card with a header.
 * @param {string} title - The title of the section.
 * @returns {HTMLDivElement} - The section element.
 */

function createSection(title) {
  const div = document.createElement("div");
  div.className = "card";
  const header = document.createElement("h2");
  header.className = "section-header";
  header.innerText = title;
  div.appendChild(header);
  return div;
}

/**
 * Utility function to create a styled input element.
 * @param {string} placeholder - Placeholder text for the input.
 * @param {string} type - Type of input (default: text).
 * @returns {HTMLInputElement}
 */
function createInput(placeholder = "", type = "text") {
  const input = document.createElement("input");
  input.className = "input";
  input.placeholder = placeholder;
  input.type = type;
  return input;
}

// Section containers
let ownershipSection, employeeSection, foundingSection, fundraiseSection, totalRaisedSection, countrySection;

document.addEventListener("DOMContentLoaded", async function () {
  const app = document.getElementById("app");
  let savedConfig = {};

  // Fetch saved configuration from the backend
  try {
    const res = await fetch("/get-configuration/");
    const data = await res.json();
    if (data.status === "success") {
      savedConfig = data.data || {};
    }
  } catch (e) {
    console.error("Failed to load saved config:", e);
  }

  // Constants used in various selectors
  const ownershipTypes = [
    "Private", "Private Sub", "Private Equity", "Public", "Public Sub",
    "Government", "Venture Capital", "Non-Profit", "Seed"
  ];
  const employeeOwnershipTypes = ["Private", "Private Sub", "Private Equity", "Public", "Public Sub",
    "Government", "Venture Capital", "Non-Profit", "Seed"];
  const countries = [ "USA", "Canada", "UK", "Germany", "France", "Albania", "Andorra", "Armenia", "Austria", "Azerbaijan", "Belarus", "Belgium", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus", "Czech Republic (Czechia)", "Denmark", "Estonia", "Finland", "Georgia", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kazakhstan (partly in EU)", "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine", "United Kingdom", "Vatican City (Holy See)", "All others" ];

  // Ownership Section
  ownershipSection = createSection("Ownership");
  ownershipTypes.forEach(type => {
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.justifyContent = "space-between";
    row.style.alignItems = "center";
    row.style.marginBottom = "12px";

    const label = document.createElement("span");
    label.innerText = type;
    label.style.flex = "1";
    label.style.fontWeight = "500";

    const select = document.createElement("select");
    select.className = "select";
    select.style.width = "120px";
    ["", 1, 2, 3, 4].forEach(val => {
      const opt = document.createElement("option");
      opt.value = val;
      opt.innerText = val || "Select";
      select.appendChild(opt);
    });
    select.value = savedConfig?.Ownership?.[type] ?? "";

    row.append(label, select);
    ownershipSection.appendChild(row);
  });
  app.appendChild(ownershipSection);

  // Employee Count Section
  employeeSection = createSection("Employee Count");
[1, 2, 3].forEach(tier => {
  const tierLabel = document.createElement("h3");
  tierLabel.innerText = "Tier " + tier;
  tierLabel.style.fontWeight = "700";
  tierLabel.style.fontSize = "18px";
  tierLabel.style.marginBottom = "12px";
  tierLabel.style.color = "#3B87AD";
  employeeSection.appendChild(tierLabel);

  employeeOwnershipTypes.forEach(ownership => {
    const row = document.createElement("div");
    row.className = "grid";
    row.style.display = "grid";
    row.style.gridTemplateColumns = "1.5fr 1fr 1fr 0.5fr";
    // Add more gap between columns 2 and 3 (between Max and Min inputs)
    row.style.columnGap = "20px"; // Increased from 12px to 20px
    row.style.rowGap = "12px";
    row.style.marginBottom = "12px";

    const label = document.createElement("span");
    label.innerText = ownership;

    const inputMax = createInput("Max", "number");
    const inputMin = createInput("Min", "number");

    const prev = savedConfig.FTE_Count?.[`tier_${tier}`]?.[ownership];
    if (prev) {
      inputMax.value = prev.max ?? "";
      inputMin.value = prev.min ?? "";
    }

    const tierSpan = document.createElement("span");
    tierSpan.innerText = tier;
    tierSpan.style.textAlign = "center";
    tierSpan.style.minWidth = "20px";

    row.append(label, inputMax, inputMin, tierSpan);
    employeeSection.appendChild(row);
  });
});
app.appendChild(employeeSection);
  // Founding Year
  foundingSection = createSection("Founding Year");
  [1, 2, 3].forEach(tier => {
    const row = document.createElement("div");
    row.style.display = "grid";
    row.style.gridTemplateColumns = "1fr 1fr";
    row.style.gap = "12px";
    row.style.marginBottom = "12px";

    const label = document.createElement("span");
    label.innerText = "Tier " + tier;
    label.className = "label";

    const input = createInput("YYYY", "text");
    input.maxLength = 4;
    input.value = savedConfig.founding_year?.[`tier_${tier}`] ?? "";

    row.append(label, input);
    foundingSection.appendChild(row);
  });
  app.appendChild(foundingSection);

  // Fundraise Year
  fundraiseSection = createSection("Fundraise Year");
  [1, 2, 3].forEach(tier => {
    const row = document.createElement("div");
    row.style.display = "grid";
    row.style.gridTemplateColumns = "1fr 1fr";
    row.style.gap = "12px";
    row.style.marginBottom = "12px";

    const label = document.createElement("span");
    label.innerText = "Tier " + tier;
    label.className = "label";

    const input = createInput("YYYY", "text");
    input.maxLength = 4;
    input.value = savedConfig.fundraiser_year?.[`tier_${tier}`] ?? "";

    row.append(label, input);
    fundraiseSection.appendChild(row);
  });
  app.appendChild(fundraiseSection);

  // Total Raised Section
totalRaisedSection = createSection("Total Raised");
["Private Equity", "Others"].forEach(group => {
  const groupLabel = document.createElement("h3");
  groupLabel.innerText = group;
  groupLabel.style.fontWeight = "700";
  groupLabel.style.fontSize = "18px";
  groupLabel.style.marginBottom = "12px";
  groupLabel.style.color = "#3B87AD";
  totalRaisedSection.appendChild(groupLabel);

  [1, 2, 3].forEach(tier => {
    const row = document.createElement("div");
    row.className = "grid";
    row.style.display = "grid";
    row.style.gridTemplateColumns = "1fr 1fr 1fr 0.5fr";
    row.style.gap = "12px";
    row.style.marginBottom = "12px";

    const label = document.createElement("span");
    label.innerText = group;

    const input = createInput("Max Amount", "number");
    const key = group;
    input.value = savedConfig.total_raised?.[`tier_${tier}`]?.[key] ?? "";

    const tierSpan = document.createElement("span");
    tierSpan.innerText = tier;
    tierSpan.style.textAlign = "center";
    tierSpan.style.minWidth = "20px";

    row.append(label, input, tierSpan);
    totalRaisedSection.appendChild(row);
  });
});
app.appendChild(totalRaisedSection);

  // Country
  countrySection = createSection("Country");
  countries.forEach(country => {
    const row = document.createElement("div");
    row.style.display = "grid";
    row.style.gridTemplateColumns = "1fr 120px";
    row.style.alignItems = "center";
    row.style.gap = "12px";
    row.style.marginBottom = "8px";

    const label = document.createElement("span");
    label.innerText = country;

    const select = document.createElement("select");
    select.className = "select";
    ["", 1, 2, 3, 4].forEach(val => {
      const opt = document.createElement("option");
      opt.value = val;
      opt.innerText = val || "Select";
      select.appendChild(opt);
    });
    select.value = savedConfig.country?.[country] ?? "";

    row.append(label, select);
    countrySection.appendChild(row);
  });
  app.appendChild(countrySection);

  // Submit Button
  const submitBtn = document.createElement("button");
  submitBtn.innerText = "Submit Configuration";
  submitBtn.style.cssText = `
    padding: 12px 24px; background-color: #007bff; color: #fff;
    border: none; border-radius: 4px; font-size: 16px; cursor: pointer;
    margin-top: 32px; display: block; margin-left: auto; margin-right: auto;
  `;

  submitBtn.addEventListener("click", () => {
    const config = {
      country: {}, Ownership: {},
      FTE_Count: { tier_1: {}, tier_2: {}, tier_3: {} },
      founding_year: {}, fundraiser_year: {},
      total_raised: { tier_1: {}, tier_2: {}, tier_3: {} }
    };

    // Ownership
    const ownershipEls = ownershipSection.querySelectorAll("select");
    ownershipTypes.forEach((type, i) => {
      config.Ownership[type] = parseInt(ownershipEls[i].value) || null;
    });

    // Country
    const countryEls = countrySection.querySelectorAll("select");
    countries.forEach((country, i) => {
      config.country[country] = parseInt(countryEls[i].value) || null;
    });

    // Founding Year
    foundingSection.querySelectorAll("input").forEach((input, i) => {
      config.founding_year[`tier_${i + 1}`] = input.value;
    });

    // Fundraiser Year
    fundraiseSection.querySelectorAll("input").forEach((input, i) => {
      config.fundraiser_year[`tier_${i + 1}`] = input.value;
    });

    // FTE Count
    employeeSection.querySelectorAll("div.grid").forEach((row) => {
      const inputs = row.querySelectorAll("input");
      if (inputs.length) {
        const [max, min] = inputs;
        const ownership = row.children[0].innerText;
        const tier = row.children[3].innerText;
        const maxVal = max.value.trim();
        const minVal = min.value.trim();
        if (maxVal || minVal) {
          config.FTE_Count[`tier_${tier}`][ownership] = {
            max: maxVal ? parseInt(maxVal) : null,
            min: minVal ? parseInt(minVal) : null
          };
        }
      }
    });

    // Total Raised
    totalRaisedSection.querySelectorAll("div.grid").forEach((row) => {
      const [label, input, tierEl] = row.children;
      const group = label.innerText;
      const tier = `tier_${tierEl.innerText}`;
      const key = group === "Others" ? "Others" : "private_equity";
      const value = input.value.trim();
      if (value) {
        config.total_raised[tier][key] = parseInt(value);
      }
    });

  // Send configuration to backend
  fetch("/submit-configuration/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken")
  },
  body: JSON.stringify(config)
})
  .then((res) => {
    if (!res.ok) throw new Error("Failed to submit");
    return res.json();
  })
  .then((data) => {
    if (data.status === "success") {
      showPopup("Configuration saved successfully!");
      if (data.next) {
        window.location.href = data.next;
      }
    } else {
      throw new Error(data.message || "Unknown error");
    }
  })
  .catch(() => showPopup("Error saving configuration.", true));
  });

  app.appendChild(submitBtn);

  // ---------------- Utility: Get CSRF Token from Cookies ----------------
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function showPopup(message, isError = false) {
    const popup = document.getElementById("popup-message");
    popup.innerText = message;
    popup.classList.toggle("error", isError);
    popup.style.display = "block";
    popup.style.opacity = "1";
    setTimeout(() => {
      popup.style.opacity = "0";
      setTimeout(() => {
        popup.style.display = "none";
      }, 300);
    }, 3000);
  }
});
