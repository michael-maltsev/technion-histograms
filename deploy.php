<?php

require_once 'deploy_course_names.php';
require_once 'Parsedown.php';

// For the IDE, defined in deploy_course_names.php.
if (!defined('COURSE_NAMES')) {
    define('COURSE_NAMES', []);
}

$courses = [];
$stats = [
    'courses' => 0,
    'semesters' => 0,
    'histograms' => 0,
    'histograms_empty' => 0,
    'staff' => 0,
    'staff_empty' => 0,
    'format_old' => 0,
    'format_new' => 0,
];
$dir = new DirectoryIterator('.');
foreach ($dir as $fileinfo) {
    if ($fileinfo->getFilename()[0] == '.' || !$fileinfo->isDir()) {
        // Skip .git in addition to . and ..
        continue;
    }

    $course = $fileinfo->getFilename();
    if (str_starts_with($course, '_mismatch_') || strlen($course) == 6) {
        continue;
    }

    process_course($course, $stats);
    $courses[] = $course;
}

natsort($courses);
$root_text = "# הטכניון - מאגר היסטוגרמות\n\n";
foreach ($courses as $course) {
    $course_name = course_friendly_name($course);
    $root_text .= "[$course_name]($course/)  \n";
}

file_put_contents('README.md', $root_text);
file_put_contents('index.html', markdown_to_page('הטכניון - מאגר היסטוגרמות', $root_text));

echo "Processed {$stats['histograms']} histograms in {$stats['courses']} courses\n";
echo "Old,new format: {$stats['format_old']},{$stats['format_new']}\n";
$without_staff_info = $stats['semesters'] - $stats['staff'];
echo "{$stats['semesters']} course-semesters, {$stats['staff']} with staff info ({$stats['staff_empty']} empty), $without_staff_info without\n";
echo "Empty histogram details: {$stats['histograms_empty']}\n";

function process_course($course, &$stats) {
    $stats['courses']++;

    $root_text = '';
    $toc = '';
    $root_object = [];

    $semesters = [];
    $dir = new DirectoryIterator($course);
    foreach ($dir as $fileinfo) {
        if ($fileinfo->isDot() || !$fileinfo->isDir()) {
            continue;
        }

        $semesters[] = $fileinfo->getFilename();
    }

    rsort($semesters, SORT_NATURAL);
    foreach ($semesters as $semester) {
        $stats['semesters']++;
        $semester_object = [];

        $semester_pretty = semester_friendly_name($semester);

        $root_text .= "<h2 id=\"$semester\">$semester_pretty</h2>\n\n";
        $toc .= "* [$semester_pretty](#$semester)\n";

        $staff_filename = "$course/$semester/Staff.json";
        if (!is_file($staff_filename)) {
            $staff_filename_international = "$course/$semester/Staff_international.json";
            if (is_file($staff_filename_international)) {
                rename($staff_filename_international, $staff_filename);
            }
        }

        if (is_file($staff_filename)) {
            $stats['staff']++;

            $data = json_decode(file_get_contents($staff_filename), true);
            if (count($data) > 0) {
                $root_text .= staff_data_to_table($data) . "\n";
                $semester_object['Staff'] = $data;
            } else {
                $stats['staff_empty']++;
            }
        } else {
            //log_warning("$course/$semester: Semester with missing staff info");
        }

        $categories = [
            'Exam_A' => 'מבחן מועד א\'',
            'Final_A' => 'סופי מועד א\'',
            'Exam_B' => 'מבחן מועד ב\'',
            'Final_B' => 'סופי מועד ב\'',
            'Exam_C' => 'מבחן מועד ג\'',
            'Final_C' => 'סופי מועד ג\'',
            'Finals' => 'סופי',
        ];

        $category_count = 0;
        foreach ($categories as $category => $category_name) {
            $filename = "$course/$semester/$category.json";
            if (!is_file($filename)) {
                $filename_international = "$course/$semester/{$category}_international.json";
                if (is_file($filename_international)) {
                    rename($filename_international, $filename);
                }
            }

            $image_filename = "$course/$semester/$category.png";
            if (!is_file($image_filename)) {
                $image_filename_international = "$course/$semester/{$category}_international.png";
                if (is_file($image_filename_international)) {
                    rename($image_filename_international, $image_filename);
                }
            }

            if (!is_file($filename)) {
                if (is_file($image_filename)) {
                    log_warning("$course/$semester/$category: Image with missing data");
                }
                continue;
            }

            if (!is_file($image_filename)) {
                log_warning("$course/$semester/$category: Data with missing image");
            } else {
                $size = getimagesize($image_filename);
                if (!$size) {
                    log_warning("$course/$semester/$category: Data with invalid image (!!!)");
                } else if ($size[0] == 800 && $size[1] == 450) {
                    $stats['format_old']++;
                } else if ($size[0] == 720 && $size[1] == 405) {
                    $stats['format_new']++;
                } else {
                    log_warning("$course/$semester/$category: Data with invalid image dimensions: {$size[0]}x{$size[1]}");
                }
            }

            $stats['histograms']++;
            $category_count++;

            $data = json_decode(file_get_contents($filename), true);

            // Less files - less timeout errors in Github Pages deployment.
            unlink($filename);

            if (intval($data['max']) >= 200) {
                log_warning("$course/$semester/$category: Data with invalid max: {$data['max']}");
            }

            $non_empty_count = count(array_filter($data, function ($item) {
                // Trim with non-breaking spaces.
                // https://stackoverflow.com/a/27990195
                return trim($item, " \t\n\r\0\x0B\xC2\xA0") != '';
            }));
            if ($non_empty_count == 0) {
                $stats['histograms_empty']++;
            } else if ($non_empty_count < count($data)) {
                log_warning("$course/$semester/$category: Partial data");
            }

            $root_text .= "<h3 id=\"$semester-$category\">$category_name</h3>\n\n";
            $root_text .= "![$semester $category]($semester/$category.png)\n\n";
            $root_text .= histogram_data_to_table($data) . "\n";
            $toc .= "  * [$category_name](#$semester-$category)\n";

            $semester_object[$category] = $data;
        }

        if ($category_count > 0) {
            $root_object[$semester] = $semester_object;
        }
    }

    $course_name = course_friendly_name($course);
    $note = '**הערה**: ' .
        'מאגר ההיסטוגרמות הוקם עבור [CheeseFork](https://cheesefork.cf/), כלי בניית מערכת שעות עבור סטודנטים בטכניון. ' .
        'באתר בו אתם גולשים ניתן לעיין בהיסטוגרמות, אך הדרך היותר נוחה היא לעיין בהיסטוגרמות, ובמידע נוסף כגון חוות דעת של סטודנטים, באתר CheeseFork.';

    $content = "# $course_name\n\n$note\n\n$toc\n$root_text";

    file_put_contents("$course/README.md", $content);
    file_put_contents("$course/index.html", markdown_to_page("$course_name - הטכניון - מאגר היסטוגרמות", $content));
    file_put_contents("$course/index.json", json_encode($root_object, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    file_put_contents("$course/index.min.json", json_encode($root_object, JSON_UNESCAPED_UNICODE));
}

function log_warning($msg) {
    echo "Warning: $msg\n";
}

function histogram_data_to_table($data) {
    $mapping = [
        'students' => 'סטודנטים',
        'passFail' => 'עברו/נכשלו',
        'passPercent' => 'אחוז עוברים',
        'min' => 'ציון מינימלי',
        'max' => 'ציון מקסימלי',
        'average' => 'ממוצע',
        'median' => 'חציון'
    ];

    $row1 = '|';
    $row2 = '|';
    $row3 = '|';
    foreach ($mapping as $key => $val) {
        $row1 .= " $val |";
        $row2 .= " ---- |";
        $row3 .= " {$data[$key]} |";
    }

    return "$row1\n$row2\n$row3\n";
}

function staff_data_to_table($data) {
    $mapping = [
        'name' => 'איש סגל',
        'title' => 'תפקיד'
    ];

    $header = '|';
    $separator = '|';
    foreach ($mapping as $key => $val) {
        $header .= " $val |";
        $separator .= " ---- |";
    }

    $rows = '';
    foreach ($data as $stuff_person) {
        $rows .= '|';
        foreach ($mapping as $key => $val) {
            $rows .= " {$stuff_person[$key]} |";
        }
        $rows .= "\n";
    }

    return "$header\n$separator\n$rows";
}

function markdown_to_page($title, $content) {
    $title_html = htmlspecialchars($title);
    $content_html = Parsedown::instance()->text($content);
    return <<<EOF
<!DOCTYPE html>
<html lang="he" dir="rtl">
  <head>
    <meta charset="utf-8">
    <link rel="shortcut icon" href="https://michael-maltsev.github.io/technion-histograms/favicon.ico">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="google-site-verification" content="Nps3LEfDaHCQolJfA4KJfgEA1c4hv6R04bCUijxBwdY" />
    <title>$title_html</title>
    <style>
      /* stolen from thebestmotherfucking.website */
      body{font-family:Open Sans,Arial;color:#454545;font-size:16px;margin:2em auto;max-width:800px;padding:1em;line-height:1.4;text-align:justify}html.contrast body{color:#050505}html.contrast blockquote{color:#11151a}html.contrast blockquote:before{color:#262626}html.contrast a{color:#0051c9}html.contrast a:visited{color:#7d013e}html.contrast span.wr{color:#800}html.contrast span.mfw{color:#4d0000}@media screen and (prefers-color-scheme:light){html.inverted{background-color:#000}html.inverted body{color:#d9d9d9}html.inverted div#contrast,html.inverted div#invmode{color:#fff;background-color:#000}html.inverted blockquote{color:#d3c9be}html.inverted blockquote:before{color:#b8b8b8}html.inverted a{color:#00a2e7}html.inverted a:visited{color:#ca1a70}html.inverted span.wr{color:#d24637}html.inverted span.mfw{color:#b00000}html.inverted.contrast{background-color:#000}html.inverted.contrast body{color:#fff}html.inverted.contrast div#contrast,html.inverted.contrast div#invmode{color:#fff;background-color:#000}html.inverted.contrast blockquote{color:#f8f6f5}html.inverted.contrast blockquote:before{color:#e5e5e5}html.inverted.contrast a{color:#44c7ff}html.inverted.contrast a:visited{color:#e9579e}html.inverted.contrast span.wr{color:#db695d}html.inverted.contrast span.mfw{color:#ff0d0d}}@media (prefers-color-scheme:dark){html:not(.inverted){background-color:#000}html:not(.inverted) body{color:#d9d9d9}html:not(.inverted) div#contrast,html:not(.inverted) div#invmode{color:#fff;background-color:#000}html:not(.inverted) blockquote{color:#d3c9be}html:not(.inverted) blockquote:before{color:#b8b8b8}html:not(.inverted) a{color:#00a2e7}html:not(.inverted) a:visited{color:#ca1a70}html:not(.inverted) span.wr{color:#d24637}html:not(.inverted) span.mfw{color:#b00000}html:not(.inverted).contrast{background-color:#000}html:not(.inverted).contrast body{color:#fff}html:not(.inverted).contrast div#contrast,html:not(.inverted).contrast div#invmode{color:#fff;background-color:#000}html:not(.inverted).contrast blockquote{color:#f8f6f5}html:not(.inverted).contrast blockquote:before{color:#e5e5e5}html:not(.inverted).contrast a{color:#44c7ff}html:not(.inverted).contrast a:visited{color:#e9579e}html:not(.inverted).contrast span.wr{color:#db695d}html:not(.inverted).contrast span.mfw{color:#ff0d0d}html.inverted html{background-color:#fefefe}}a{color:#07a}a:visited{color:#941352}.noselect{-webkit-touch-callout:none;-webkit-user-select:none;-khtml-user-select:none;-moz-user-select:none;-ms-user-select:none;user-select:none}span.citneed{vertical-align:top;font-size:.7em;padding-left:.3em}small{font-size:.4em}p.st{margin-top:-1em}div.fancyPositioning div.picture-left{float:left;width:40%;overflow:hidden;margin-right:1em}div.fancyPositioning div.picture-left img{width:100%}div.fancyPositioning div.picture-left figure{margin:10px}div.fancyPositioning div.picture-left figure figcaption{font-size:.7em}div.fancyPositioning div.tleft{float:left;width:55%}div.fancyPositioning div.tleft p:first-child{margin-top:0}div.fancyPositioning:after{display:block;content:"";clear:both}ul li img{height:1em}blockquote{color:#456;margin-left:0;margin-top:2em;margin-bottom:2em}blockquote span{float:left;margin-left:1rem;padding-top:1rem}blockquote author{display:block;clear:both;font-size:.6em;margin-left:2.4rem;font-style:oblique}blockquote author:before{content:"- ";margin-right:1em}blockquote:before{font-family:Times New Roman,Times,Arial;color:#666;content:open-quote;font-size:2.2em;font-weight:600;float:left;margin-top:0;margin-right:.2rem;width:1.2rem}blockquote:after{content:"";display:block;clear:both}@media screen and (max-width:500px){body{text-align:right}div.fancyPositioning div.picture-left,div.fancyPositioning div.tleft{float:none;width:inherit}blockquote span{width:80%}blockquote author{padding-top:1em;width:80%;margin-left:15%}blockquote author:before{content:"";margin-right:inherit}}span.visited{color:#941352}span.visited-maroon{color:#85144b}span.wr{color:#c0392b;font-weight:600;text-decoration:underline}div#contrast{color:#000;top:10px}div#contrast,div#invmode{cursor:pointer;position:fixed;right:10px;font-size:.8em;text-decoration:underline;-webkit-touch-callout:none;-webkit-user-select:none;-khtml-user-select:none;-moz-user-select:none;-ms-user-select:none;user-select:none}div#invmode{color:#fff;background-color:#000;top:34px;padding:2px 5px}@media screen and (max-width:1080px){div#contrast,div#invmode{position:absolute}}span.sb{color:#00e}span.sb,span.sv{cursor:not-allowed}span.sv{color:#551a8b}span.foufoufou{color:#444;font-weight:700}span.foufoufou:before{content:"";display:inline-block;width:1em;height:1em;margin-left:.2em;margin-right:.2em;background-color:#444}span.foufivfoufivfoufiv{color:#454545;font-weight:700}span.foufivfoufivfoufiv:before{content:"";display:inline-block;width:1em;height:1em;margin-left:.2em;margin-right:.2em;background-color:#454545}span.mfw{color:#730000}a.kopimi,a.kopimi img.kopimi{display:block;margin-left:auto;margin-right:auto}a.kopimi img.kopimi{height:2em}p.fakepre{font-family:monospace;font-size:.9em}
      img {
        max-width: 100%;
      }
      table {
        /* Scrollable: https://stackoverflow.com/a/62451601 */
        display: block;
        overflow-x: auto;
        white-space: nowrap;
        /* Border */
        border-collapse: collapse;
      }
      table th, table td {
        border: 1px solid #454545;
        padding: 10px;
      }
    </style>
  </head>
  <body>
    $content_html
  </body>
</html>

EOF;
}

function semester_friendly_name($semester) {
    $year = intval(substr($semester, 0, 4));
    $semesterCode = substr($semester, 4);

    switch ($semesterCode) {
        case '01':
            return 'חורף ' . $year . '-' . ($year + 1);

        case '02':
            return 'אביב ' . ($year + 1);

        case '03':
            return 'קיץ ' . ($year + 1);

        default:
            return $semester;
    }
}

function course_friendly_name($course) {
    $dict = COURSE_NAMES;
    if (!isset($dict[$course])) {
        return $course;
    }

    return  "$course - {$dict[$course]}";
}
