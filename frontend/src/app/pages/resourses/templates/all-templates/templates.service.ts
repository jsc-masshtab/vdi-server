import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '@shared/types';


@Injectable()
export class TemplatesService {

    constructor(private service: Apollo) { }

    public params: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    public getAllTemplates(filter?, refresh?): QueryRef<any, any> {

        let query: string = `
            query resources(
                $limit: Int,
                $offset: Int,
                $ordering:ShortString
            ){
                templates_with_count(
                    limit: $limit,
                    offset: $offset,
                    ordering: $ordering
                ){
                    count
                    vms {
                        id
                        verbose_name
                        status
                        controller {
                            id
                            verbose_name
                        }
                    }
                }
            }
        `

        if (filter.controller_id) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $resource_pool_id: UUID, $node_id: UUID, $ordering:ShortString) {
                controller(id_:$controller_id) {
                    id
                    templates(cluster_id: $cluster_id, resource_pool_id: $resource_pool_id, node_id: $node_id, ordering: $ordering) {
                        verbose_name
                        template {
                            id
                            verbose_name
                        }
                        id
                        status
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.params.nameSort,
                ...filter,
                refresh
            }
        });
    }

    public getTemplate(id: string, controller_address: string, refresh: boolean): QueryRef<any, any> {

        let query: string = ` query resources($id: UUID, $controller_address: UUID) {
                                template(template_id: $id, controller_id: $controller_address) {
                                    verbose_name
                                    description
                                    os_type
                                    os_version
                                    cpu_count
                                    memory_count
                                    tablet
                                    domain_tags {
                                        colour
                                        verbose_name
                                    }
                                    ha_enabled
                                    disastery_enabled
                                    remote_access
                                    spice_stream
                                    status
                                    user_power_state
                                    boot_type
                                    start_on_boot
                                    resource_pool {
                                        id
                                        verbose_name
                                    }
                                }
                            }`

        if (refresh) {
          query = ` query resources($id: UUID, $controller_address: UUID, $refresh: Boolean) {
                      template(template_id: $id, controller_id: $controller_address, refresh: $refresh) {
                          verbose_name
                          description
                          os_type
                          os_version
                          cpu_count
                          memory_count
                          tablet
                          domain_tags {
                              colour
                              verbose_name
                          }
                          ha_enabled
                          disastery_enabled
                          remote_access
                          spice_stream
                          status
                          user_power_state
                          boot_type
                          start_on_boot
                          resource_pool {
                              id
                              verbose_name
                          }
                      }
                  }`
        }
        return this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                id,
                controller_address,
                refresh
            }
        });
    }

    public attachVeilUtils(data) {
        return this.service.mutate<any>({
            mutation: gql` mutation resources($id: UUID!, $controller_id: UUID!) {
                            attachVeilUtils(domain_id: $id, controller_id: $controller_id) {
                                ok
                            }
                        }
                    `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }
}
