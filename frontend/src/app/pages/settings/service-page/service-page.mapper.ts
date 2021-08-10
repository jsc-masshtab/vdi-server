enum Status {
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
    serviceStatus: Status
}

export class MutationServiceInfo implements IMutationServiceInfo {
    ok: boolean
    serviceStatus: Status
}

export class ServicePageMapper {

    public serverQueryModelToClientModel(apiModel: IQueryApiModel): QueryServiceInfo {
        const clientModel =  new QueryServiceInfo();     
        clientModel.serviceName = apiModel.service_name;
        clientModel.verboseName = apiModel.verbose_name;
        clientModel.status = apiModel.status;
        
        return clientModel; 
    }

    public serverMutationModelToClientModel(apiModel: IMutationApiModel): MutationServiceInfo {
        const clientModel =  new MutationServiceInfo();     
        clientModel.ok = apiModel.ok;
        clientModel.serviceStatus = apiModel.service_status;
        
        return clientModel; 
    }
}
