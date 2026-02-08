import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR, PPStructureV3

input_file = "./tests/fixtures/resnet.pdf"

def F1():
    print("OCR")
    ocr = PaddleOCR()
    output = ocr.predict(input_file)
    for res in output:
        res.save_all(save_path="output") ## Save the current image's structured result in JSON format
    print("all done")

def F2():
    print("F2")
    from paddleocr import PaddleOCRVL
    pipeline = PaddleOCRVL(device='gpu:0', use_queues=False)
    output = pipeline.predict(input_file, use_queues=False)
    for res in output:
        print(res)
    print("all done")

def F3():
    pipeline = PPStructureV3(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False
    )
    output = pipeline.predict(input_file)
    for res in output:
        res.save_all(save_path="./output")

if __name__ == "__main__":
    F1()
