import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';


@Injectable()
export class PoolDetailsService {

    constructor(private service: Apollo) { }


    public removePool(idPool: number) {
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

    public getPool(pool_id: string | number, type: string, controller_address: string): Observable<any> {
        if (type === 'automated') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String, $controller_address: String) {
                                pool(pool_id: $pool_id, controller_address: $controller_address) {
                                    pool_id
                                    verbose_name
                                    pool_type
                                    vms {
                                        id
                                        verbose_name
                                        template {
                                            verbose_name
                                        }
                                        user {
                                            username
                                        }
                                        status
                                    }
                                    controller {
                                        address
                                    }
                                    initial_size
                                    reserve_size
                                    total_size
                                    vm_name_template
                                    users {
                                        username
                                    }
                                    cluster {
                                        verbose_name
                                    }
                                    node {
                                        verbose_name
                                    }
                                    datapool {
                                        verbose_name
                                    }
                                    template {
                                        verbose_name
                                    }
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id,
                    controller_address
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }

        if (type === 'static') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String, $controller_address: String) {
                                pool(pool_id: $pool_id, controller_address: $controller_address) {
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
                    pool_id,
                    controller_address
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }
    }

    public addVMStaticPool(poolId: number, vmIds: []) {
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
                pool_id: poolId,
                vm_ids: vmIds
            }
        });
    }

    public removeVMStaticPool(poolId: number, vmIds: []) {
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
                pool_id: poolId,
                vm_ids: vmIds
            }
        });
    }

    public assignVmToUser(vmId: string, usernameVM: string) {
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
                vm_id: vmId,
                username: usernameVM
            }
        });
    }

    public freeVmFromUser(vmId: string) {
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
                vm_id: vmId
            }
        });
    }

    public getAllUsersNoEntitleToPool(idPool: number): QueryRef<any, any> {
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

    public assesUsersToPool(idPool: number): QueryRef<any, any> {
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
                cluster_id: clusterId,
                node_id: nodeId,
                get_vms_in_pools: false
            }
        });
    }

    public removeUserEntitlementsFromPool(poolId: number, entitledUsers: []) {
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
                pool_id: poolId,
                entitled_users: entitledUsers,
                free_assigned_vms: true
            }
        });
    }

    public entitleUsersToPool(poolId: number, entitledUsers: []) {
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
                pool_id: poolId,
                entitled_users: entitledUsers
            }
        });
    }

    public editNamePool({id}: {id: number}, {name}: {name: string}) {
        const idPool = id;
        const newNamePool = name;
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

    public changeAutomatedPoolTotalSize({id}: {id: number}, {new_total_size}: {new_total_size: number}) {
        const idPool = id;
        const newTotalSize = new_total_size;
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

    public changeAutomatedPoolReserveSize({id}: {id: number}, {reserve_size}: {reserve_size: number}) {
        const idPool = id;
        const newReserveSize = reserve_size;
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

    public changeTemplateForVmAutomatedPool({id}: {id: number}, {vm_name_template}: {vm_name_template: string}) {
        const idPool = id;
        const newNameTemplate = vm_name_template;
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
