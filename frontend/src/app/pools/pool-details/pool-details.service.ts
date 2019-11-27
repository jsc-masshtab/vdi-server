import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';


@Injectable()
export class PoolDetailsService {

    constructor(private service: Apollo) { }


    public removePool(pool_id: number) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($pool_id: UUID) {
                            removePool(pool_id: $pool_id) {
                                ok
                            }
                        }
            `,
            variables: {
                method: 'POST',
                pool_id
            }
        });
    }

    public getPool(pool_id: string | number, type: string): Observable<any> {
        if (type === 'automated') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String) {
                                pool(pool_id: $pool_id) {
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
                                        state
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
                    pool_id
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }

        if (type === 'static') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String) {
                                pool(pool_id: $pool_id) {
                                    verbose_name
                                    pool_type
                                    vms {
                                        verbose_name
                                        id
                                        user {
                                            username
                                        }
                                        status
                                        state
                                    }
                                    controller {
                                        address
                                    }
                                    cluster_id
                                    node_id
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
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }
    }

    public addVMStaticPool(pool_id: number, vm_ids: []) { // +
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($pool_id: ID!,$vm_ids: [UUID]!) {
                                addVmsToStaticPool(pool_id: $pool_id, vm_ids: $vm_ids) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id,
                vm_ids
            }
        });
    }

    public removeVMStaticPool(pool_id: number, vm_ids: []) { // +
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
                pool_id,
                vm_ids
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

    public getAllUsersNoEntitleToPool(pool_id: number): QueryRef<any, any> {  // -
        return  this.service.watchQuery({
             query:  gql` query pools($pool_id: String, $entitled: Boolean) {
                            pool(pool_id: $pool_id) {
                                users(entitled: $entitled) {
                                    username
                                }
                            }
                        }
                     `,
            variables: {
                method: 'GET',
                entitled: false,
                pool_id
            }
         });
    }

    public removeUserEntitlementsFromPool(poolId: number, entitledUsers: []) { // -
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

    public entitleUsersToPool(poolId: number, entitledUsers: []) { // -
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

    public getAllVms(cluster_id: string, node_id: string): QueryRef<any, any> { // +
        return  this.service.watchQuery({
            query:  gql` query vms($cluster_id: String,$node_id:String) {
                                    vms(cluster_id: $cluster_id,node_id: $node_id) {
                                        id
                                        verbose_name
                                    }
                                }
                    `,
            variables: {
                method: 'GET',
                cluster_id,
                node_id,
                get_vms_in_pools: false
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
