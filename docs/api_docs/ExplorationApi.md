---
layout: default
parent: API
---

# ExplorationApi

All URIs are relative to *https://model-service.worldmodelers.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_models_post**](ExplorationApi.md#list_models_post) | **POST** /list_models | Obtain a list of current models
[**model_config_model_name_get**](ExplorationApi.md#model_config_model_name_get) | **GET** /model_config/{ModelName} | Obtain configurations for a given model.
[**model_info_model_name_get**](ExplorationApi.md#model_info_model_name_get) | **GET** /model_info/{ModelName} | Get basic metadata information for a specified model.
[**model_outputs_model_name_get**](ExplorationApi.md#model_outputs_model_name_get) | **GET** /model_outputs/{ModelName} | Obtain information on a given model&#x27;s outputs.
[**model_parameters_model_name_get**](ExplorationApi.md#model_parameters_model_name_get) | **GET** /model_parameters/{ModelName} | Obtain information about a model&#x27;s parameters.

# **list_models_post**
> AvailableModels list_models_post()

Obtain a list of current models

Request a list of currently available models.

### Example
```python
import requests

response = requests.post('https://model-service.worldmodelers.com/list_models')
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AvailableModels**](AvailableModels.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_config_model_name_get**
> ModelConfig model_config_model_name_get(model_name)

Obtain configurations for a given model.

Submit a model name and receive all configurations for the given model.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/model_config/malnutrition_model')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**ModelConfig**](ModelConfig.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_info_model_name_get**
> Model model_info_model_name_get(model_name)

Get basic metadata information for a specified model.

Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/model_info/malnutrition_model')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**Model**](Model.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_outputs_model_name_get**
> list[Variable] model_outputs_model_name_get(model_name)

Obtain information on a given model's outputs.

Submit a model name and receive information about the output variables produced by this model.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/model_outputs/malnutrition_model')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**list[Variable]**](Variable.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_parameters_model_name_get**
> list[Parameter] model_parameters_model_name_get(model_name)

Obtain information about a model's parameters.

Submit a model name and receive information about the parameters used by this model. Specific parameters are used on a per-configuration basis.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/model_parameters/malnutrition_model')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**list[Parameter]**](Parameter.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

