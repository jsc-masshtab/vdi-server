import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { timer,Observable } from 'rxjs';
import { switchMap ,map} from 'rxjs/operators';




@Injectable()
export class PoolsService  {

    constructor(private service: Apollo) {}

    public getAllPools(obs?:boolean): Observable<any> {
        const obs$ = timer(0,60000);

        if(obs) {
            return  obs$.pipe(switchMap(()=> { return this.service.watchQuery({
                query:  gql` query allPools {
                                    pools {
                                        id
                                        name
                                        settings {
                                            initial_size
                                            reserve_size
                                        }
                                        vms {
                                            id
                                        }
                                    }  
                                }
                            
                
                        `,
                variables: {
                    method: 'GET'
                }
            }).valueChanges.pipe(map(data => data.data['pools'])); } ));
        } else {
            return this.service.watchQuery({
                query:  gql` query allPools {
                                    pools {
                                        id
                                        name
                                        settings {
                                            initial_size
                                            reserve_size
                                        }
                                        vms {
                                            id
                                        }
                                    }  
                                }
                            
                
                        `,
                variables: {
                    method: 'GET'
                }
            }).valueChanges.pipe(map(data => data.data['pools'])); };
    }

    public removePool(pool_id:number) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation RemovePool($id: Int) {
                                removePool(id: $id) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                id: pool_id
            }
        })
    }

    public getPool(id:number): Observable<any> {

        return  this.service.watchQuery({
            query:  gql`  query getPool($id: Int) {
                        pool(id: $id) {
                            name
                            state {
                                available {
                                    name
                                    template {
                                        name
                                    }
                                    node {
                                        verbose_name
                                    }
                                }
                            }
                            settings {
                                initial_size
                                reserve_size
                            }
                        }
                    }`,
            variables: {
                method: 'GET',
                id: id
            }
        }).valueChanges.pipe(map(data => data.data['pool'])); 
    };
    

    public createDinamicPool(name: string,template_id: string,cluster_id: string,node_id: string,datapool_id: string,initial_size: number,reserve_size: number) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddPool($name: String!,$template_id: String,$cluster_id: String,$node_id: String,$datapool_id: String,$initial_size: Int,$reserve_size: Int) {
                                addPool(name: $name, template_id: $template_id,cluster_id: $cluster_id,node_id: $node_id,datapool_id: $datapool_id,initial_size: $initial_size,reserve_size: $reserve_size) {
                                    id
                                }
                            }
            `,
            variables: {
                method: 'POST',
                name: name,
                template_id: template_id,
                cluster_id: cluster_id,
                node_id: node_id,
                datapool_id: datapool_id,
                initial_size: initial_size,
                reserve_size: reserve_size
            }
        })
    }

    public createStaticPool(name: string,cluster_id: string,node_id: string,datapool_id: string,vm_ids_list:string[]) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddPool($name: String!,$cluster_id: String,$node_id: String,$datapool_id: String,$vm_ids_list: [String]) {
                                addStaticPool(name: $name,cluster_id: $cluster_id,node_id: $node_id,datapool_id: $datapool_id,vm_ids_list: $vm_ids_list) {
                                    id
                                }
                            }
            `,
            variables: {
                method: 'POST',
                name: name,
                cluster_id: cluster_id,
                node_id: node_id,
                datapool_id: datapool_id,
                vm_ids_list: vm_ids_list
            }
        })
    }
}