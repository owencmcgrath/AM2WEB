import { NextRequest, NextResponse } from "next/server";
import plist from "simple-plist";
import logging from "../../utils/logging";
import fs from "fs";
import { writeFile } from "fs/promises";
import os from "os";

export async function POST(req: NextRequest) {
  logging.info("[INFO] - Received POST request to /api/parse-xml");
  //save uploaded XML to a temporary file for parsing
  const xml = await req.text();
  logging.info(`[DEBUG] - Received XML length: ${xml.length}`);
  const tempDir = os.tmpdir();
  const tempPath = `${tempDir}/library.xml`;
  await writeFile(tempPath, xml);
  logging.info(`[DEBUG] - XML written to temporary file: ${tempPath}`);

  try {
    //parse the XML file using simple-plist
    const data = plist.readFileSync(tempPath) as any;
    logging.info("[INFO] - Parsed plist file successfully");

    //access the Tracks dictionary
    const tracks = data.Tracks;
    if (!tracks || typeof tracks !== "object") {
      logging.error("[ERROR] - No 'Tracks' dictionary found in plist file");
      return NextResponse.json(
        { error: "No 'Tracks' found in plist file" },
        { status: 400 }
      );
    }
    logging.info(`[DEBUG] - Found ${Object.keys(tracks).length} tracks`);

    //collect song titles and log each track
    let titles: string[] = [];
    for (const trackId in tracks) {
      const track = tracks[trackId];
      if (track.Name) {
        logging.info(`[INFO] - Track ${trackId} title: ${track.Name}`);
        titles.push(track.Name);
      } else {
        logging.error(`[ERROR] - Track ${trackId} has no title`);
      }
    }

    logging.info(`[INFO] - Finished parsing all tracks. Total titles: ${titles.length}`);
    return NextResponse.json({ titles });
  } catch (err) {
    logging.error("[ERROR] - Exception in parseSongsFromPlistFile", err);
    const errorMessage = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json(
      { error: "Failed to parse plist", details: errorMessage },
      { status: 400 }
    );
  } finally {
    //clean up the temporary file
    try {
      fs.unlinkSync(tempPath);
      logging.info(`[DEBUG] - Temporary file deleted: ${tempPath}`);
    } catch (cleanupErr) {
      logging.error("[ERROR] - Failed to delete temporary file", cleanupErr);
    }
  }
}