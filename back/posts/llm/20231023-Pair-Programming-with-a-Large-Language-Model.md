---
title: 20231023-Pair-Programming-with-a-Large-Language-Model
date: 2023-10-23
tags:
  - ai
  - llm
  - software_engineer
  - course
---
## TL;DR
LLM 可以幫助程式設計師包含：改進現有程式碼、簡化code、寫測試、優化程式除錯及解釋程式碼，使用流程為(1)建立prompt (2)取得結果 (3) 輸出結果，為了程式重複使用，會使用template機制讓呼叫比較簡單。

Palm - google 的llm模型
有三個組成
- API Key
- GEN AI library
model裡面選擇 chat bison vs text bison 差別是多次對話跟一次對話
大致上使用流程
1. create a prompt
2. completion
3. output result
## Getting start
```python
from utils import get_api_key
import os
import google.generativeai as palm
from google.api_core import client_options as client_options_lib

palm.configure(
    api_key=get_api_key(),
    transport="rest",
    client_options=client_options_lib.ClientOptions(
        api_endpoint=os.getenv("GOOGLE_API_BASE"),
    )
)
models = [m for m in palm.list_models() 
          if 'generateText' 
          in m.supported_generation_methods]
model_bison = models[0]
model_bison
from google.api_core import retry
@retry.Retry()
def generate_text(prompt,
                  model=model_bison,
                  temperature=0.0):
    return palm.generate_text(prompt=prompt,
                              model=model,
                              temperature=temperature)
```

### process
1. create a prompt `prompt = "Show me how to iterate across a list in Python."`
2. completion `completion = generate_text(prompt)`
3. output `print(completion.result)`
## String template
```python
import os
from utils import get_api_key
import google.generativeai as palm
from google.api_core import client_options as client_options_lib

palm.configure(
    api_key=get_api_key(),
    transport="rest",
    client_options=client_options_lib.ClientOptions(
        api_endpoint=os.getenv("GOOGLE_API_BASE"),
    )
)
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model_bison = models[0]
model_bison
from google.api_core import retry
@retry.Retry()
def generate_text(prompt, 
                  model=model_bison, 
                  temperature=0.0):
    return palm.generate_text(prompt=prompt,
                              model=model,
                              temperature=temperature)
prompt_template = """
{priming}

{question}

{decorator}

Your solution:
"""
priming_text = "You are an expert at writing clear, concise, Python code."
question = "create a doubly linked list"
decorator = "Insert comments for each line of code."
prompt = prompt_template.format(priming=priming_text,
                                question=question,
                                decorator=decorator)
```
### prompt_template
- priming: 類似前情提要/背景
- question: 要問的問題
- decorator: 修飾回答樣式
## Pair Progaming scenarios
### 1. improve existing code
```python
prompt_template = """
I don't think this code is the best way to do it in Python, can you help me?

{question}

Please explain, in detail, what you did to improve it.
"""
question = """
def func_x(array)
  for i in range(len(array)):
    print(array[i])
"""
completion = generate_text(
    prompt = prompt_template.format(question=question)
)
print(completion.result)
prompt_template = """
I don't think this code is the best way to do it in Python, can you help me?

{question}

Please explore ***multiple ways*** of solving the problem, and explain each.
"""
completion = generate_text(
    prompt = prompt_template.format(question=question)
)
print(completion.result)
prompt_template = """
I don't think this code is the best way to do it in Python, can you help me?

{question}

Please explore multiple ways of solving the problem, 
and tell me which is ***the most Pythonic***
"""
completion = generate_text(
    prompt = prompt_template.format(question=question)
)
print(completion.result)
```
### 2. simplify code
```python
prompt_template = """
Can you please simplify this code for a linked list in Python?

{question}

Explain in detail what you did to modify it, and why.
"""
question = """
class Node:
  def __init__(self, dataval=None):
    self.dataval = dataval
    self.nextval = None

class SLinkedList:
  def __init__(self):
    self.headval = None

list1 = SLinkedList()
list1.headval = Node("Mon")
e2 = Node("Tue")
e3 = Node("Wed")
list1.headval.nextval = e2
e2.nextval = e3

"""
completion = generate_text(
    prompt = prompt_template.format(question=question)
)
print(completion.result)
```
### 3. write test cases
```python
prompt_template = """
Can you please create test cases in code for this Python code?

{question}

Explain in detail what these test cases are designed to achieve.
"""
# Note that the code I'm using here was output in the previous
# section. Your output code may be different.
question = """
class Node:
  def __init__(self, dataval=None):
    self.dataval = dataval
    self.nextval = None

class SLinkedList:
  def __init__(self):
    self.head = None

def create_linked_list(data):
  head = Node(data[0])
  for i in range(1, len(data)):
    node = Node(data[i])
    node.nextval = head
    head = node
  return head

list1 = create_linked_list(["Mon", "Tue", "Wed"])
"""
completion = generate_text(
    prompt = prompt_template.format(question=question)
)
print(completion.result)
```
### 4. Make code more efficient
```python
prompt_template = """
Can you please make this code more efficient?

{question}

Explain in detail what you changed and why.
"""
question = """
# Returns index of x in arr if present, else -1
def binary_search(arr, low, high, x):
    # Check base case
    if high >= low:
        mid = (high + low) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] > x:
            return binary_search(arr, low, mid - 1, x)
        else:
            return binary_search(arr, mid + 1, high, x)
    else:
        return -1

# Test array
arr = [ 2, 3, 4, 10, 40 ]
x = 10

# Function call
result = binary_search(arr, 0, len(arr)-1, x)

if result != -1:
    print("Element is present at index", str(result))
else:
    print("Element is not present in array")

"""
completion = generate_text(
    prompt = prompt_template.format(question=question)
)
print(completion.result)
```
有時候輸出有可能會錯
### 5.  Debug your code
```python
prompt_template = """
Can you please help me to debug this code?

{question}

Explain in detail what you found and why it was a bug.
"""
# I deliberately introduced a bug into this code! Let's see if the LLM can find it.
# Note -- the model can't see this comment -- but the bug is in the
# print function. There's a circumstance where nodes can be null, and trying
# to print them would give a null error.
question = """
class Node:
   def __init__(self, data):
      self.data = data
      self.next = None
      self.prev = None

class doubly_linked_list:
   def __init__(self):
      self.head = None

# Adding data elements
   def push(self, NewVal):
      NewNode = Node(NewVal)
      NewNode.next = self.head
      if self.head is not None:
         self.head.prev = NewNode
      self.head = NewNode

# Print the Doubly Linked list in order
   def listprint(self, node):
       print(node.data),
       last = node
       node = node.next

dllist = doubly_linked_list()
dllist.push(12)
dllist.push(8)
dllist.push(62)
dllist.listprint(dllist.head)
"""
completion = generate_text(
    prompt = prompt_template.format(question=question),
    temperature = 0.7
)
print(completion.result)
```
- temperature>0會有一些隨機性，所以可能要檢查
###  Technical Debt

```python
import os
from utils import get_api_key
import google.generativeai as palm
from google.api_core import client_options as client_options_lib

palm.configure(
    api_key=get_api_key(),
    transport="rest",
    client_options=client_options_lib.ClientOptions(
        api_endpoint=os.getenv("GOOGLE_API_BASE"),
    )
)
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model_bison = models[0]
model_bison
from google.api_core import retry
@retry.Retry()
def generate_text(prompt, 
                  model=model_bison, 
                  temperature=0.0):
    return palm.generate_text(prompt=prompt,
                              model=model,
                              temperature=temperature)
```
一個很複雜的code
```swift
#@title Complex Code Block
# Note: Taken from https://github.com/lmoroney/odmlbook/blob/63c0825094b2f44efc5c4d3226425a51990e73d6/BookSource/Chapter08/ios/cats_vs_dogs/CatVsDogClassifierSample/ModelDataHandler/ModelDataHandler.swift
CODE_BLOCK = """
// Copyright 2019 The TensorFlow Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import CoreImage
import TensorFlowLite
import UIKit


/// An inference from invoking the `Interpreter`.
struct Inference {
  let confidence: Float
  let label: String
}

/// Information about a model file or labels file.
typealias FileInfo = (name: String, extension: String)

/// Information about the MobileNet model.
enum MobileNet {
  static let modelInfo: FileInfo = (name: "converted_model", extension: "tflite")
}

/// This class handles all data preprocessing and makes calls to run inference on a given frame
/// by invoking the `Interpreter`. It then formats the inferences obtained and returns the top N
/// results for a successful inference.
class ModelDataHandler {

  // MARK: - Public Properties

  /// The current thread count used by the TensorFlow Lite Interpreter.
  let threadCount: Int

  let resultCount = 1

  // MARK: - Model Parameters

  let batchSize = 1
  let inputChannels = 3
  let inputWidth = 224
  let inputHeight = 224

  // MARK: - Private Properties

  /// List of labels from the given labels file.
  private var labels: [String] = ["Cat", "Dog"]

  /// TensorFlow Lite `Interpreter` object for performing inference on a given model.
  private var interpreter: Interpreter

  /// Information about the alpha component in RGBA data.
  private let alphaComponent = (baseOffset: 4, moduloRemainder: 3)

  // MARK: - Initialization

  /// A failable initializer for `ModelDataHandler`. A new instance is created if the model and
  /// labels files are successfully loaded from the app's main bundle. Default `threadCount` is 1.
  init?(modelFileInfo: FileInfo, threadCount: Int = 1) {
    let modelFilename = modelFileInfo.name

    // Construct the path to the model file.
    guard let modelPath = Bundle.main.path(
      forResource: modelFilename,
      ofType: modelFileInfo.extension
      ) else {
        print("Failed to load the model file with name: \(modelFilename).")
        return nil
    }

    // Specify the options for the `Interpreter`.
    self.threadCount = threadCount
    var options = InterpreterOptions()
    options.threadCount = threadCount
    do {
      // Create the `Interpreter`.
      interpreter = try Interpreter(modelPath: modelPath, options: options)
    } catch let error {
      print("Failed to create the interpreter with error: \(error.localizedDescription)")
      return nil
    }

  }

  // MARK: - Public Methods

  /// Performs image preprocessing, invokes the `Interpreter`, and process the inference results.
  func runModel(onFrame pixelBuffer: CVPixelBuffer) -> [Inference]? {
    let sourcePixelFormat = CVPixelBufferGetPixelFormatType(pixelBuffer)
    assert(sourcePixelFormat == kCVPixelFormatType_32ARGB ||
      sourcePixelFormat == kCVPixelFormatType_32BGRA ||
      sourcePixelFormat == kCVPixelFormatType_32RGBA)


    let imageChannels = 4
    assert(imageChannels >= inputChannels)

    // Crops the image to the biggest square in the center and scales it down to model dimensions.
    let scaledSize = CGSize(width: inputWidth, height: inputHeight)
    guard let thumbnailPixelBuffer = pixelBuffer.centerThumbnail(ofSize: scaledSize) else {
      return nil
    }

    let outputTensor: Tensor
    do {
      // Allocate memory for the model's input `Tensor`s.
      try interpreter.allocateTensors()

      // Remove the alpha component from the image buffer to get the RGB data.
      guard let rgbData = rgbDataFromBuffer(
        thumbnailPixelBuffer,
        byteCount: batchSize * inputWidth * inputHeight * inputChannels
        ) else {
          print("Failed to convert the image buffer to RGB data.")
          return nil
      }

      // Copy the RGB data to the input `Tensor`.
      try interpreter.copy(rgbData, toInputAt: 0)

      // Run inference by invoking the `Interpreter`.
      try interpreter.invoke()

      // Get the output `Tensor` to process the inference results.
      outputTensor = try interpreter.output(at: 0)
    } catch let error {
      print("Failed to invoke the interpreter with error: \(error.localizedDescription)")
      return nil
    }

    let results = [Float32](unsafeData: outputTensor.data) ?? []

    // Process the results.
    let topNInferences = getTopN(results: results)

    // Return the inference time and inference results.
    return topNInferences
  }

  // MARK: - Private Methods

  /// Returns the top N inference results sorted in descending order.
  private func getTopN(results: [Float]) -> [Inference] {
    // Create a zipped array of tuples [(labelIndex: Int, confidence: Float)].
    let zippedResults = zip(labels.indices, results)

    // Sort the zipped results by confidence value in descending order.
    let sortedResults = zippedResults.sorted { $0.1 > $1.1 }.prefix(resultCount)

    // Return the `Inference` results.
    return sortedResults.map { result in Inference(confidence: result.1, label: labels[result.0]) }
  }

  /// Loads the labels from the labels file and stores them in the `labels` property.
  private func loadLabels(fileInfo: FileInfo) {
    let filename = fileInfo.name
    let fileExtension = fileInfo.extension
    guard let fileURL = Bundle.main.url(forResource: filename, withExtension: fileExtension) else {
      fatalError("Labels file not found in bundle. Please add a labels file with name " +
        "\(filename).\(fileExtension) and try again.")
    }
    do {
      let contents = try String(contentsOf: fileURL, encoding: .utf8)
      labels = contents.components(separatedBy: .newlines)
    } catch {
      fatalError("Labels file named \(filename).\(fileExtension) cannot be read. Please add a " +
        "valid labels file and try again.")
    }
  }

  /// Returns the RGB data representation of the given image buffer with the specified `byteCount`.
  ///
  /// - Parameters
  ///   - buffer: The pixel buffer to convert to RGB data.
  ///   - byteCount: The expected byte count for the RGB data calculated using the values that the
  ///       model was trained on: `batchSize * imageWidth * imageHeight * componentsCount`.
  ///   - isModelQuantized: Whether the model is quantized (i.e. fixed point values rather than
  ///       floating point values).
  /// - Returns: The RGB data representation of the image buffer or `nil` if the buffer could not be
  ///     converted.
  private func rgbDataFromBuffer(
    _ buffer: CVPixelBuffer,
    byteCount: Int
    ) -> Data? {
    CVPixelBufferLockBaseAddress(buffer, .readOnly)
    defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
    guard let mutableRawPointer = CVPixelBufferGetBaseAddress(buffer) else {
      return nil
    }
    let count = CVPixelBufferGetDataSize(buffer)
    let bufferData = Data(bytesNoCopy: mutableRawPointer, count: count, deallocator: .none)
    var rgbBytes = [Float](repeating: 0, count: byteCount)
    var index = 0
    for component in bufferData.enumerated() {
      let offset = component.offset
      let isAlphaComponent = (offset % alphaComponent.baseOffset) == alphaComponent.moduloRemainder
      guard !isAlphaComponent else { continue }
      rgbBytes[index] = Float(component.element) / 255.0
      index += 1
    }

    return rgbBytes.withUnsafeBufferPointer(Data.init)

  }
}

// MARK: - Extensions

extension Data {
  /// Creates a new buffer by copying the buffer pointer of the given array.
  ///
  /// - Warning: The given array's element type `T` must be trivial in that it can be copied bit
  ///     for bit with no indirection or reference-counting operations; otherwise, reinterpreting
  ///     data from the resulting buffer has undefined behavior.
  /// - Parameter array: An array with elements of type `T`.
  init<T>(copyingBufferOf array: [T]) {
    self = array.withUnsafeBufferPointer(Data.init)
  }
}

extension Array {
  /// Creates a new array from the bytes of the given unsafe data.
  ///
  /// - Warning: The array's `Element` type must be trivial in that it can be copied bit for bit
  ///     with no indirection or reference-counting operations; otherwise, copying the raw bytes in
  ///     the `unsafeData`'s buffer to a new array returns an unsafe copy.
  /// - Note: Returns `nil` if `unsafeData.count` is not a multiple of
  ///     `MemoryLayout<Element>.stride`.
  /// - Parameter unsafeData: The data containing the bytes to turn into an array.
  init?(unsafeData: Data) {

    guard unsafeData.count % MemoryLayout<Element>.stride == 0 else { return nil }
    #if swift(>=5.0)
    self = unsafeData.withUnsafeBytes { .init($0.bindMemory(to: Element.self)) }
    #else
    self = unsafeData.withUnsafeBytes {
      .init(UnsafeBufferPointer<Element>(
        start: $0,
        count: unsafeData.count / MemoryLayout<Element>.stride
      ))
    }
    #endif  // swift(>=5.0)
  }
}
"""
```
```python
prompt_template = """
Can you please explain how this code works?

{question}

Use a lot of detail and make it as clear as possible.
"""
completion = generate_text(
    prompt = prompt_template.format(question=CODE_BLOCK)
)
print(completion.result)
```

## Ref
- https://learn.deeplearning.ai/pair-programming-llm/