# Sample data credits

All sample images in `data/samples/` are sourced from [Wikimedia
Commons](https://commons.wikimedia.org) under licenses that permit reuse.
None depict real patients or any identifiable clinical data — the
"healthcare" category deliberately uses staged PPE/training-facility
imagery only. Fetched with [`scripts/fetch_commons_image.py`](../scripts/fetch_commons_image.py).

## manufacturing/

| File | Source | License | Attribution |
|---|---|---|---|
| `warehouse_1.jpg` | [Workers drive Forklifts laden with USAID goods inside a large warehouse](https://commons.wikimedia.org/wiki/File:Workers_drive_Forklifts_laden_with_USAID_goods_inside_a_large_warehouse_-_20110826-FS-LSC-0222_-_Flickr_-_USDAgov.jpg) | Public Domain (US government work) | USDA Photo by Lance Cheung — no attribution required |
| `factory_1.jpg` | [Machine working in a factory while cutting material on a production line](https://commons.wikimedia.org/wiki/File:Machine_working_in_a_factory_while_cutting_material_on_a_production_line_in_the_workshop.jpg) | CC BY 2.0 | Shixart1985 |

## healthcare/

*(Staged/training imagery only — no real patients, no clinical data.)*

| File | Source | License | Attribution |
|---|---|---|---|
| `ppe_workers_1.jpg` | [Healthcare workers wearing PPE 03](https://commons.wikimedia.org/wiki/File:Healthcare_workers_wearing_PPE_03.jpg) | CC0 | No attribution required |
| `ppe_delivery_1.jpg` | [31 FW delivers 70,000 COVID-19 PPE items to local Italian hospitals](https://commons.wikimedia.org/wiki/File:31_FW_delivers_70,000_COVID-19_PPE_items_to_local_Italian_hospitals_(6548281).jpg) | Public Domain (US government work) | No attribution required |
| `medical_team_1.jpg` | [Medical Team testing blood samples at the training facility in Strensall](https://commons.wikimedia.org/wiki/File:Medical_Team_testing_blood_samples_at_the_training_facility_in_Strensall._MOD_45159008.jpg) | UK Open Government Licence v1.0 | Graham Harrison, MOD |

## video_analytics/

| File | Source | License | Attribution |
|---|---|---|---|
| `street_1.jpg` | [8 Av 33 St intersection](https://commons.wikimedia.org/wiki/File:8_Av_33_St_intersection_vc.jpg) | CC BY 2.0 | Alex ([Flickr](https://www.flickr.com/photos/alex92287/3026940648/)) |
| `street_2.jpg` | [Corner of E 7th Ave and N 16th St, Ybor City, Tampa](https://commons.wikimedia.org/wiki/File:Corner_of_E_7th_Ave_and_N_16th_St_in_downtown_Ybor_City,_Tampa,_Florida,_at_night_on_28_October_2023.jpg) | CC BY-SA 4.0 | MatthewHoobin |

## Regenerating or extending this dataset

```bash
python scripts/fetch_commons_image.py "<search query>" <count>
```

Prints candidate images with their license and a direct download URL for
each match under the query — check the license before downloading and add
an entry here for anything you add.
