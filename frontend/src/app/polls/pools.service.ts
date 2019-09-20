import { Injectable } from '@angular/core';
import { Apollo } from 'apollo-angular';
import gql from 'graphql-tag';
import { timer, Observable } from 'rxjs';
import { switchMap, map } from 'rxjs/operators';


@Injectable()
export class PoolsService {

    constructor(private service: Apollo) { }

    public getAllPools(obs?: boolean): Observable<any> {
        const obs$ = timer(0, 60000);

        if (obs) {
            return obs$.pipe(switchMap(() => {
                return this.service.watchQuery({
                    query: gql` query allPools {
                                    pools {
                                        id
                                        name
                                        vms {
                                            id
                                        }
                                        desktop_pool_type
                                        controller {
                                            ip
                                        }
                                        users {
                                            username
                                        }
                                    }  
                                }
                        `,
                    variables: {
                        method: 'GET'
                    }
                }).valueChanges.pipe(map(data => data.data['pools']));
            }));
        } else {
            return this.service.watchQuery({
                query: gql` query allPools {
                                    pools {
                                        id
                                        name
                                        vms {
                                            id
                                        }
                                        desktop_pool_type
                                        controller {
                                            ip
                                        }
                                        users {
                                            username
                                        }
                                    }  
                                }
                        `,
                variables: {
                    method: 'GET'
                }
            }).valueChanges.pipe(map(data => data.data['pools']));
        };
    }

    public removePool(pool_id: number) {
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

    public getPool(id: number, type: string): Observable<any> {

        if (type === 'automated') {
            return this.service.watchQuery({
                query: gql`  query getPool($id: Int) {
                                pool(id: $id) {
                                    name
                                    desktop_pool_type
                                    vms {
                                        id
                                        name
                                        template {
                                            name
                                        }
                                        state
                                        user {
                                            username
                                        }
                                    }  
                                    controller {
                                        ip
                                    }
                                    settings {
                                        initial_size
                                        reserve_size
                                        total_size
                                    }
                                    users {
                                        username
                                    }
                                    pool_resources_names {
                                        cluster_name
                                        node_name
                                        datapool_name
                                        template_name
                                    }
                                }
                            }`,
                variables: {
                    method: 'GET',
                    id: id
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }

        if (type === 'static') {
            return this.service.watchQuery({
                query: gql`  query getPool($id: Int) {
                                pool(id: $id) {
                                    name
                                    desktop_pool_type
                                    vms {
                                        name
                                        state
                                        id
                                        user {
                                            username
                                        }
                                    }  
                                    controller {
                                        ip
                                    }
                                    settings {
                                        cluster_id
                                        node_id
                                    }
                                    users {
                                        username
                                    }
                                    pool_resources_names {
                                        cluster_name
                                        node_name
                                        datapool_name
                                    }
                                }
                            }`,
                variables: {
                    method: 'GET',
                    id: id
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }
    };


    public createDinamicPool(name: string, template_id: string, cluster_id: string, node_id: string, datapool_id: string, initial_size: number, reserve_size: number, total_size: number) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddPool($name: String!,$template_id: String,$cluster_id: String,$node_id: String,$datapool_id: String,$initial_size: Int,$reserve_size: Int,$total_size: Int) {
                                addPool(name: $name, template_id: $template_id,cluster_id: $cluster_id,node_id: $node_id,datapool_id: $datapool_id,initial_size: $initial_size,reserve_size: $reserve_size,total_size:$total_size) {
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
                reserve_size: reserve_size,
                total_size: total_size
            }
        })
    }

    public createStaticPool(name: string, cluster_id: string, node_id: string, datapool_id: string, vm_ids_list: string[]) {
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

    public addVMStaticPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddVms($pool_id: Int!,$vm_ids: [ID]!) {
                                addVmsToStaticPool(pool_id: $pool_id,vm_ids: $vm_ids) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: pool_id,
                vm_ids: vm_ids
            }
        })
    }

    public removeVMStaticPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation RemoveVms($pool_id: Int!,$vm_ids: [ID]!) {
                                removeVmsFromStaticPool(pool_id: $pool_id,vm_ids: $vm_ids) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: pool_id,
                vm_ids: vm_ids
            }
        })
    }

    public assignVmToUser(vm_id: number, username: string) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AssignVmToUser($vm_id: ID!,$username: String!) {
                                assignVmToUser(vm_id: $vm_id,username: $username) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                vm_id: vm_id,
                username: username
            }
        })
    }

    public freeVmFromUser(vm_id: number) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation FreeVmFromUser($vm_id: ID!) {
                                freeVmFromUser(vm_id: $vm_id) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                vm_id: vm_id
            }
        })
    }
}