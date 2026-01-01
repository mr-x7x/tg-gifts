const fs = require("fs-extra");
const axios = require("axios");

const dataPath = "data/gifts.json";
const imagesDir = "images";
const jsonDir = "json";

(async () => {
  try {
    const gifts = JSON.parse(fs.readFileSync(dataPath, "utf8"));

    await fs.ensureDir(imagesDir);
    await fs.ensureDir(jsonDir);

    for (const gift of gifts) {
      const { id, image_url, animation_url } = gift;
      if (!id) continue;

      const imagePath = `${imagesDir}/${id}.png`;
      const jsonPath = `${jsonDir}/${id}.json`;

      console.log(`⬇️ Downloading ${id} ...`);

      if (image_url) {
        const img = await axios.get(image_url, { responseType: "arraybuffer" });
        fs.writeFileSync(imagePath, img.data);
      }

      if (animation_url) {
        const anim = await axios.get(animation_url, { responseType: "arraybuffer" });
        fs.writeFileSync(jsonPath, anim.data);
      }
    }

    console.log("✅ All files downloaded successfully!");
  } catch (err) {
    console.error("❌ Error:", err.message);
    process.exit(1);
  }
})();
