/* Local draft preview only. Uploads and edits still use the protected admin forms. */
(() => {
  "use strict";
  const root = document.querySelector('[data-boss-root][data-mode="admin"]');
  if (!root || !document.getElementById("bossPreviewAvatar")) return;
  const id = (name) => document.getElementById(name);
  const name = id("bossNameInput"),
    file = id("bossAvatarFile");
  let saved = JSON.parse(root.dataset.bossBootstrap).state;
  let imageDraft = "",
    sequence = 0,
    imageError = "";

  function render() {
    const draftName = name.value.trim() || saved.name;
    id("bossPreviewName").textContent = draftName;
    id("bossPreviewTitle").textContent =
      saved.status === "victory"
        ? `The crew conquered ${draftName}.`
        : saved.status === "paused"
          ? "The raid is taking a breather."
          : "Take your next shot.";
    id("bossPreviewAvatar").src = imageDraft || saved.avatar_url;
    id("bossPreviewAvatar").classList.toggle(
      "custom-avatar",
      Boolean(imageDraft || saved.avatar_custom),
    );
    id("bossPreviewHealth").max = saved.max_hp;
    id("bossPreviewHealth").value = saved.hp;
    id("bossPreviewPercent").textContent =
      (((saved.max_hp - saved.hp) / saved.max_hp) * 100).toFixed(2) +
      "% defeated";
    id("bossPreviewRemaining").textContent =
      `${saved.hp.toLocaleString()} HP left · ${saved.raiders} raiders united`;
    id("bossPreviewMessage").textContent =
      imageError ||
      (imageDraft || draftName !== saved.name
        ? "Unsaved appearance preview. Save the name and upload the avatar separately below."
        : "Showing saved appearance.");
  }
  name.addEventListener("input", render);
  file.addEventListener("change", () => {
    const current = ++sequence,
      selected = file.files[0];
    imageDraft = "";
    imageError = "";
    if (!selected) return render();
    if (
      !/\.(png|jpe?g|webp)$/i.test(selected.name) ||
      (selected.type &&
        !["image/png", "image/jpeg", "image/webp"].includes(selected.type)) ||
      selected.size > 4 * 1024 * 1024
    ) {
      imageError = "Select a PNG, JPG, JPEG or WebP image up to 4 MB.";
      return render();
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (current !== sequence) return;
      // Decode locally before display. Server-side Pillow validation still
      // controls what may be saved; this preview never authorizes an upload.
      const image = new Image();
      image.onload = () => {
        if (current !== sequence) return;
        imageDraft = reader.result;
        render();
      };
      image.onerror = () => {
        if (current !== sequence) return;
        imageError =
          "This image cannot be previewed. Choose a valid image file.";
        render();
      };
      image.src = reader.result;
    };
    reader.onerror = () => {
      if (current !== sequence) return;
      imageError = "Could not read that image. Select it again.";
      render();
    };
    reader.readAsDataURL(selected);
    render();
  });
  document.addEventListener("boss:admin-state", (event) => {
    saved = event.detail;
    render();
  });
  render();
})();
