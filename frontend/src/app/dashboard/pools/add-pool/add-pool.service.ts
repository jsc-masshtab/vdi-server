import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class AddPoolService {

    constructor(private service: Apollo) { }

    public getData(type, data: any = {}): QueryRef<any, any> {
        let query: string = '';

        if (type == 'controllers') {
            query = `query 
                controllers {
                    controllers {
                        id
                        verbose_name
                    }
                }
            `
        }

        if (type == 'clusters') {
            query = `query 
                controllers($id_: UUID) {
                    controller(id_: $id_) {
                        id
                        clusters {
                            id
                            verbose_name
                        }
                    }
                }
            `
        }

        if (type == 'nodes') {
            query = `query 
                controllers($id_: UUID, $cluster_id: UUID) {
                    controller(id_: $id_) {
                        id
                        nodes(cluster_id: $cluster_id) {
                            id
                            verbose_name
                        }
                    }
                }
            `
        }

        if (type == 'data_pools') {
            query = `query 
                controllers($id_: UUID, $cluster_id: UUID, $node_id: UUID) {
                    controller(id_: $id_) {
                        id
                        data_pools(cluster_id: $cluster_id, node_id: $node_id) {
                            id
                            verbose_name
                        }
                    }
                }
            `
        }

        if (type == 'vms') {
            query = `query 
                controllers($id_: UUID, $cluster_id: UUID, $node_id: UUID, $data_pool_id: UUID) {
                    controller(id_: $id_) {
                        id
                        vms(cluster_id: $cluster_id, node_id: $node_id, data_pool_id: $data_pool_id) {
                            id
                            verbose_name
                        }
                    }
                }
            `
        }

        if (type == 'templates') {
            query = `query 
                controllers($id_: UUID, $cluster_id: UUID, $node_id: UUID, $data_pool_id: UUID) {
                    controller(id_: $id_) {
                        id
                        templates(cluster_id: $cluster_id, node_id: $node_id, data_pool_id: $data_pool_id) {
                            id
                            verbose_name
                        }
                    }
                }
            `
        }
        
        return this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ...data
            }
        });
    }

    addStaticPool(data) { 
        let query: string = ` mutation 
            pools(
                $connection_types: [PoolConnectionTypes!]
                $vms: [VmInput!]!
                $node_id: UUID!
                $controller_id: UUID!
                $datapool_id: UUID!
                $verbose_name: String!
                $cluster_id: UUID!
            ) {
                addStaticPool(
                    connection_types: $connection_types
                    vms: $vms
                    node_id: $node_id
                    controller_id: $controller_id
                    datapool_id: $datapool_id
                    verbose_name: $verbose_name
                    cluster_id: $cluster_id
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
                $node_id: UUID!
                $controller_id: UUID!
                $datapool_id: UUID!
                $verbose_name: String!
                $cluster_id: UUID!
                $template_id: UUID!

                $vm_name_template: String!

                $increase_step: Int
                $reserve_size: Int
                $total_size: Int
                $initial_size: Int
                $create_thin_clones: Boolean
            ) {
                addDynamicPool(
                    connection_types: $connection_types
                    node_id: $node_id
                    controller_id: $controller_id
                    datapool_id: $datapool_id
                    verbose_name: $verbose_name
                    cluster_id: $cluster_id
                    template_id: $template_id

                    vm_name_template: $vm_name_template

                    increase_step: $increase_step
                    reserve_size: $reserve_size
                    total_size: $total_size
                    initial_size: $initial_size
                    create_thin_clones: $create_thin_clones
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
