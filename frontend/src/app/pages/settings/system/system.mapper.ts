export interface ISystemResponse{
    system_info: ApiModel
  }

export interface ApiModel {
    time_zone: string
    local_time: Date
    networks_list: [{
      name: string
      ipv4: string
    }]
  }
  
export interface ISystemData {
    networksList: INetwork[]
    timezone: string
    localTime: Date
} 
export class SystemData implements  ISystemData{
    networksList: INetwork[]
    timezone: string
    localTime: Date
  }

export interface INetwork{
    name: string
    ip: string
  }  

  

export class SystemMapper {

    public serverModelToClientModel(apiModel: ApiModel): SystemData {
        const { time_zone, local_time, networks_list} = apiModel;  
        
        return {
          timezone: time_zone,
          localTime: local_time,
          networksList: networks_list.map( item => ({name: item.name, ip: item.ipv4}))
        } 
    }
}
