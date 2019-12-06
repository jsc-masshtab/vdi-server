import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class AddPoolService {

    constructor(private service: Apollo) { }

    public getAllClusters(controller_ip?: string): QueryRef<any, any> {
        if (controller_ip) {
            return this.service.watchQuery({
                query: gql`query resources($controller_ip: String) {
                                clusters(controller_ip: $controller_ip) {
                                    id
                                    verbose_name
                                }
                            }
                        `,
                variables: {
                    method: 'GET',
                    controller_ip
                }
            });
        } else {
            return this.service.watchQuery({
                query: gql` query resources {
                                clusters {
                                    id
                                    verbose_name
                                }
                            }
                        `,
                variables: {
                    method: 'GET'
                }
            });
        }
    }

    public getAllNodes(cluster_id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query resources($cluster_id: String) {
                            nodes(cluster_id: $cluster_id) {
                                id
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                cluster_id
            }
        });
    }

    public getAllDatapools(node_id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query resources($node_id: String) {
                                datapools(node_id: $node_id) {
                                    id
                                    verbose_name
                                }
                            }
                        `,
            variables: {
                method: 'GET',
                node_id
            }
        });
    }

    public getAllVms(cluster_id: string, node_id: string, datapool_id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms($cluster_id: String, $node_id:String, $datapool_id:String)  {
                            vms(cluster_id: $cluster_id, node_id: $node_id, datapool_id: $datapool_id)  {
                                id
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                get_vms_in_pools: false,
                cluster_id,
                node_id,
                datapool_id
            }
        });
    }

    public getAllTemplates(controller_ip: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms($controller_ip: String) {
                            templates(controller_ip: $controller_ip) {
                                id
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                controller_ip
            }
        });
    }

    public getAllControllers(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query controllers {
                            controllers {
                                address
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    public createDinamicPool(verbose_name: string, template_id: string, cluster_id: string,
                             node_id: string, datapool_id: string, initial_size: number,
                             reserve_size: number, total_size: number, vm_name_template: string, controller_ip: string,
                             create_thin_clones: boolean) {

        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($verbose_name: String!,$template_id: UUID!,
                                        $cluster_id: UUID!,$node_id: UUID!,
                                        $datapool_id: UUID!,$initial_size: Int,
                                        $reserve_size: Int,$total_size: Int,
                                        $vm_name_template: String,
                                        $controller_ip: String!,$create_thin_clones: Boolean)
                                {
                                addDynamicPool(verbose_name: $verbose_name, template_id: $template_id,
                                        cluster_id: $cluster_id,node_id: $node_id,
                                        datapool_id: $datapool_id,initial_size: $initial_size,
                                        reserve_size: $reserve_size,total_size:$total_size,
                                        vm_name_template: $vm_name_template,
                                        controller_ip: $controller_ip,create_thin_clones:$create_thin_clones
                                        )
                                        {
                                            ok
                                        }
                            }
            `,
            variables: {
                method: 'POST',
                verbose_name,
                template_id,
                cluster_id,
                node_id,
                datapool_id,
                initial_size,
                reserve_size,
                total_size,
                vm_name_template,
                controller_ip,
                create_thin_clones
            }
        });
    }

    public createStaticPool(verbose_name: string,  vm_ids: string[]) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($verbose_name: String!,$vm_ids: [UUID]!) {
                            addStaticPool(verbose_name: $verbose_name, vm_ids: $vm_ids)
                                {
                                    ok
                                }
                        }
            `,
            variables: {
                method: 'POST',
                verbose_name,
                vm_ids
            }
        });
    }
}
