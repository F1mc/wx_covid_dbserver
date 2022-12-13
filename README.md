# 微信小程序mongodb后端

基于Flask及MongoDB构建的数据库后端，使用docker部署
API请求模板见template_*.json

## API

### Insert
插入表单记录  
URL： https://**:*/insert  &emsp;  Method: POST  &emsp;  Header: "Content-Type: application/json"
| 字段 | 值 | describe |
|  ----  | ----  | ----|
| table | "table_v1","person_attr" | 插入表名 |
| value | json form | 实际表单内容，字段见模板 |
> 返回值: "msg":&emsp;,&emsp;"status":&emsp;,&emsp; msg中包含插入记录$_id, &emsp;有保留按照该id直接查记录的接口

### Query
请求数据记录  
URL： https://**:*/query   &emsp; Method: POST  &emsp;  Header: "Content-Type: application/json"
| 字段 | 值 | describe |
|  ----  | ----  | ----|
| type | "full_records","person","predic_result" | 查询类型 |
| table | "table_v1","person_attr" | 请求表名，并非每种type都需要 |
| uuid | uuid | 微信OpenID |

支持type：

full_records：  返回用户自今日七天内的记录，单一日期重复只返回最近的一次记录
> 需求字段： 
> 1. type: "full_records"
> 2. table: "" table为预留字段，避免有后续table版本，暂时可空缺
> 3. uuid

> 返回值示例：{"msg":"query succeed","status":1,"value":{"2022-12-07":{"_id":"63986a089f4ef3708338f4a5","date":[2022,12,7],"days_symp":0,"location":"","nc_test":null,"stamp":1670933000.8822377,"symptom":{"cw":false,"fl":false,"ks":false,"lt":false,"qc":false,"tt":true,"yt":false},"temp":36.7,"uuid":1},"2022-12-08":{"_id":"6398856a9f4ef3708338f4a6","date":[2022,12,8],"days_symp":0,"location":"","nc_test":null,"stamp":1670940010.275769,"symptom":{"cw":false,"fl":false,"ks":false,"lt":false,"qc":false,"tt":true,"yt":false},"temp":36.7,"uuid":1}}}

person：  返回用户
> 需求字段： 
> 1. type: "full_records"
> 2. uuid

返回值同上包含"msg","status","value"字段，value对应值同模板中person_attr表结构

predic_result: 预测结果，未实现，待算法对接

  
### UUID
查询用户OpenID  
URL： https://**:*/query  &emsp; Method: POST  &emsp;  Header: "Content-Type: application/json"
| 字段 | 值 | describe |
|  ----  | ----  | ----|
| code | code | 小程序给的请求code |
> 返回值: "msg":&emsp;,&emsp;"status":&emsp;,&emsp;"value":$uuid