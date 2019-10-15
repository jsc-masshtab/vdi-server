import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';


@Injectable()
export class PoolDetailsService {

    constructor(private service: Apollo) { }


    public removePool(id: number) {
        const idPool = id;
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
                id: idPool
            }
        });
    }

    public getPool(param: {id: number, type: string}): Observable<any> {
        const idPool = param.id;
        if (param.type === 'automated') {
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
                                        status
                                    }
                                    controller {
                                        ip
                                    }
                                    settings {
                                        initial_size
                                        reserve_size
                                        total_size
                                        vm_name_template
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
                    id: idPool
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }

        if (param.type === 'static') {
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
                                        status
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
                    id: idPool
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }
    }

    public addVMStaticPool(poolId: number, vmIds: []) {
        const idPool = poolId;
        const idsVms = vmIds;
        return this.service.mutate<any>({
            mutation: gql`
                            mutation AddVms($pool_id: Int!,$vm_ids: [ID]!) {
                                addVmsToStaticPool(pool_id: $pool_id, vm_ids: $vm_ids) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                vm_ids: idsVms
            }
        });
    }

    public removeVMStaticPool(poolId: number, vmIds: []) {
        const idPool = poolId;
        const idsVms = vmIds;
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
                pool_id: idPool,
                vm_ids: idsVms
            }
        });
    }

    public assignVmToUser(vmId: string, username: string) {
        const idVm = vmId;
        const usernameToVM = username;
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
                vm_id: idVm,
                username: usernameToVM
            }
        });
    }

    public freeVmFromUser(vmId: string) {
        const idVm = vmId;
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
                vm_id: idVm
            }
        });
    }

    public getAllUsersNoEntitleToPool(id: number): QueryRef<any, any> {
        const idPool = id;
        return  this.service.watchQuery({
             query:  gql` query allUsers($id: Int,$entitled: Boolean) {
                            pool(id: $id) {
                                users(entitled:$entitled) {
                                    username
                                }
                            }
                        }
                     `,
            variables: {
                method: 'GET',
                entitled: false,
                id: idPool
            }
         });
    }

    public assesUsersToPool(id: number): QueryRef<any, any> {
        const idPool = id;
        return this.service.watchQuery({
                query: gql`
                            query  AssesUsersToPool($id: Int) {
                                pool(id: $id) {
                                    users {
                                        username
                                    }
                                }
                            }
            `,
            variables: {
                method: 'POST',
                id: idPool
            }
        });
    }

    public getAllVms(clusterId: string, nodeId: string): QueryRef<any, any> {
        const idCluster = clusterId;
        const idNode = nodeId;
        return  this.service.watchQuery({
            query:  gql` query list_free_vms($cluster_id: String,$node_id:String) {
                                    list_of_vms(cluster_id: $cluster_id,node_id: $node_id) {
                                        id
                                        name
                                    }
                                }
                    `,
            variables: {
                method: 'GET',
                cluster_id: idCluster,
                node_id: idNode,
                get_vms_in_pools: false
            }
        });
    }

    public removeUserEntitlementsFromPool(poolId: number, entitledUsers: []) {
        const idPool = poolId;
        const addedUsers = entitledUsers;
        return this.service.mutate<any>({
            mutation: gql`
                            mutation RemoveUserEntitlementsFromPool($pool_id: ID,$entitled_users: [ID]) {
                                removeUserEntitlementsFromPool(pool_id: $pool_id, entitled_users: $entitled_users) {
                                    freed {
                                        name
                                    }
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                entitled_users: addedUsers,
                free_assigned_vms: true
            }
        });
    }

    public entitleUsersToPool(poolId: number, entitledUsers: []) {
        const idPool = poolId;
        const addedUsers = entitledUsers;
        return this.service.mutate<any>({
            mutation: gql`
                            mutation EntitleUsersToPool($pool_id: ID,$entitled_users: [ID]) {
                                entitleUsersToPool(pool_id: $pool_id, entitled_users: $entitled_users) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                entitled_users: addedUsers
            }
        });
    }

    public editNamePool(...params: [{id: number}, {name: string}]) {
        const idPool = params[0].id;
        const newNamePool = params[1].name;
        return this.service.mutate<any>({
            mutation: gql`
                            mutation ChangePoolName($pool_id: Int!,$new_name: String!) {
                                changePoolName(pool_id: $pool_id, new_name: $new_name) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                new_name: newNamePool
            }
        });
    }

    public changeAutomatedPoolTotalSize(...params: [{id: number}, {new_total_size: number}]) {
        const idPool = params[0].id;
        const newTotalSize = params[1].new_total_size;
        return this.service.mutate<any>({
            mutation: gql`
                        mutation ChangeAutomatedPoolTotalSize($pool_id: Int!,$new_total_size: Int!) {
                            changeAutomatedPoolTotalSize(pool_id: $pool_id, new_total_size: $new_total_size) {
                                ok
                            }
                        }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                new_total_size: newTotalSize
            }
        });
    }

    public changeAutomatedPoolReserveSize(...params: [{id: number}, {reserve_size: number}]) {
        const idPool = params[0].id;
        const newReserveSize = params[1].reserve_size;
        return this.service.mutate<any>({
            mutation: gql`
                            mutation ChangeAutomatedPoolReserveSize($pool_id: Int!,$new_reserve_size: Int!) {
                                changeAutomatedPoolReserveSize(pool_id: $pool_id, new_reserve_size: $new_reserve_size) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                new_reserve_size: newReserveSize
            }
        });
    }

    public changeTemplateForVmAutomatedPool(...params: [{id: number}, {vm_name_template: string}]) {
        const idPool = params[0].id;
        const newNameTemplate = params[1].vm_name_template;
        return this.service.mutate<any>({
            mutation: gql`
                            mutation changeTemplateForVmAutomatedPool($pool_id: Int!,$new_name_template: String!) {
                                changeVmNameTemplate(pool_id: $pool_id, new_name_template: $new_name_template) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: idPool,
                new_name_template: newNameTemplate
            }
        });
    }
}
