const API_URL = "http://127.0.0.1:8000/api/process-image";


const $input_image = document.getElementById("input_image");
const $select = document.getElementById("mode");
const $run = document.getElementById("run");
const $status = document.getElementById("status");
const $error = document.getElementById("error");
const $input_preview = document.getElementById("input_preview")
const $result_preview = document.getElementById("result_preview");


let prevUrl = null;
let prevResultUrl = null;
let isBusy = false;

$input_image.addEventListener("change", (event) => {
  const file = event.currentTarget.files?.[0] ?? null;
  if (!file) {
    $input_preview.src = null;
    $result_preview.src = null;
    return;
  }

  if (prevUrl) URL.revokeObjectURL(prevUrl);
  
  prevUrl = URL.createObjectURL(file);

  $input_preview.src = prevUrl;
});


const setBusy = (isbusy) =>{
    $run.disabled = isbusy;
    $status.textContent = isbusy ? "処理中..." : ""
    if(isbusy) $error.textContent = "";
}


$run.addEventListener("click", async (event) => {

    if(isBusy) return;
    isBusy = true;
    setBusy(isBusy);


    try{

        const file = $input_image.files?.[0];
        if(!file){
            const msg = "ファイルが選択されていません！";
            throw new Error(msg);
        }

    
        const mode = $select.value;

        const formdata = new FormData();
        formdata.append("file", file)
        formdata.append("mode", mode)

        const res = await fetch(API_URL, {method: "POST", body: formdata});
        if (!res.ok) {     // content-typeを見て、jsonならawait res.json() datail拾うのが丁寧らしい
            const msg = await res.text();
            throw new Error(msg);
        }

        // console.log(res.status, res.headers.get("content-type"));

        const blob = await res.blob();
        if (prevResultUrl) URL.revokeObjectURL(prevResultUrl);
        prevResultUrl = URL.createObjectURL(blob);
        // console.log(blob.type, blob.size);
        $result_preview.src = prevResultUrl;

    } catch(e){
        $error.textContent = "エラー: " + (e?.message ?? String(e));
    } finally{
        isBusy = false
        setBusy(isBusy)
    }



})
