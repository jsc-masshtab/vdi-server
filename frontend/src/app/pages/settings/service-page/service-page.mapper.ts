export enum Status {
    Running = 'running',
    Stoped = 'stoped',
    Failed = 'failed',
    Exited = 'exited'
}

export interface IQueryResponse{
    services: IQueryApiModel[]
  }

export interface IQueryApiModel {
    service_name: string
    verbose_name: string
    status: Status
  }
  
export interface IQueryService {
    serviceName: string
    verboseName: string
    status: Status
}

export class QueryServiceInfo implements IQueryService {
    serviceName: string
    verboseName: string
    status: Status
}

export interface IMutationResponse {
    doServiceAction: IMutationApiModel
}

export interface IMutationApiModel {
    ok: boolean,
    service_status: Status
}

export interface IMutationServiceInfo {
    ok: boolean,
    status: Status
}

export class MutationServiceInfo implements IMutationServiceInfo {
    ok: boolean
    status: Status
}

export class ServicePageMapper {

    public serverQueryModelToClientModel(apiModel: IQueryApiModel): QueryServiceInfo {
        const { service_name, verbose_name, status } = apiModel;
        return {     
            serviceName: service_name,
            verboseName: verbose_name,
            status
        } 
    }

    public serverMutationModelToClientModel(apiModel: IMutationApiModel): MutationServiceInfo {    
        
        const {ok, service_status} = apiModel; 
        return {
                ok,
                status: service_status
        } 
    }
}
