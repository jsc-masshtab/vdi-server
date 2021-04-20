import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class AddPoolService {

    constructor(private service: Apollo) { }

    public getData(type, data: any = {}): QueryRef<any, any> {
        let query: string = '';

        if (type === 'controllers') {
            query = `query
                controllers {
                    controllers {
                        id
                        verbose_name
                    }
                }
            `;
        }

        if (type === 'resource_pools') {
            query = `query
                controllers($id_: UUID) {
                    controller(id_: $id_) {
                        id
                        resource_pools {
                            id
                            verbose_name
                        }
                    }
                }
            `;
        }

        if (type === 'vms') {
            query = `query
                controllers($id_: UUID, $resource_pool_id: UUID) {
                    controller(id_: $id_) {
                        id
                        vms(resource_pool_id: $resource_pool_id, exclude_existed: true) {
                            id
                            verbose_name
                        }
                    }
                }
            `;
        }

        if (type === 'templates') {
            query = `query
                controllers($id_: UUID, $resource_pool_id: UUID) {
                    controller(id_: $id_) {
                        id
                        templates(resource_pool_id: $resource_pool_id) {
                            id
                            verbose_name
                        }
                    }
                }
            `;
        }

        return this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ...data
            }
        });
    }

    public getAllAuthenticationDirectory(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql` query auth_dirs {
                            auth_dirs {
                                id
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    addStaticPool(data) {
        let query: string = ` mutation
            pools(
                $connection_types: [PoolConnectionTypes!]
                $vms: [VmInput!]!
                $controller_id: UUID!
                $resource_pool_id: UUID!
                $verbose_name: String!
            ) {
                addStaticPool(
                    connection_types: $connection_types
                    vms: $vms
                    controller_id: $controller_id
                    resource_pool_id: $resource_pool_id
                    verbose_name: $verbose_name
                ) {
                    ok
                }
            }
        `;

        return this.service.mutate<any>({
            mutation: gql(query),
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    addDynamicPool(data) {
        let query: string = ` mutation
            pools(
                $connection_types: [PoolConnectionTypes!]
                $controller_id: UUID!
                $resource_pool_id: UUID!
                $verbose_name: String!
                $template_id: UUID!

                $vm_name_template: String!

                $increase_step: Int
                $reserve_size: Int
                $total_size: Int
                $initial_size: Int
                $create_thin_clones: Boolean
                $prepare_vms: Boolean
                $ad_cn_pattern: String
            ) {
                addDynamicPool(
                    connection_types: $connection_types
                    controller_id: $controller_id
                    resource_pool_id: $resource_pool_id
                    verbose_name: $verbose_name
                    template_id: $template_id

                    vm_name_template: $vm_name_template

                    increase_step: $increase_step
                    reserve_size: $reserve_size
                    total_size: $total_size
                    initial_size: $initial_size
                    create_thin_clones: $create_thin_clones
                    prepare_vms: $prepare_vms
                    ad_cn_pattern: $ad_cn_pattern
                ) {
                    ok
                }
            }
        `;

        return this.service.mutate<any>({
            mutation: gql(query),
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    addGuestPool(data) {
        let query: string = ` mutation
            pools(
                $connection_types: [PoolConnectionTypes!]
                $controller_id: UUID!
                $resource_pool_id: UUID!
                $verbose_name: String!
                $template_id: UUID!

                $vm_name_template: String!

                $increase_step: Int
                $reserve_size: Int
                $total_size: Int
                $initial_size: Int
                $ad_cn_pattern: String
            ) {
                addDynamicPool(
                    connection_types: $connection_types
                    controller_id: $controller_id
                    resource_pool_id: $resource_pool_id
                    verbose_name: $verbose_name
                    template_id: $template_id

                    vm_name_template: $vm_name_template

                    increase_step: $increase_step
                    reserve_size: $reserve_size
                    total_size: $total_size
                    initial_size: $initial_size
                    create_thin_clones: true
                    prepare_vms: true
                    ad_cn_pattern: $ad_cn_pattern
                    is_guest: true
                ) {
                    ok
                }
            }
        `;

        return this.service.mutate<any>({
            mutation: gql(query),
            variables: {
                method: 'POST',
                ...data
            }
        });
    }
}
